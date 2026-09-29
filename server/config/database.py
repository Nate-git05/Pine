#Database configuration file for the server
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from typing import AsyncGenerator
from redis.asyncio import (
    Redis,
    RedisError
)
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    PointIdsList,
    Filter,
    FieldCondition,
    MatchAny,
)
from openai import AsyncClient
from uuid import uuid4
from enum import StrEnum

"""Configuring databases for the server"""
#Relational 
class RelationalDatabase:
    def __init__(self, postgres_uri:str):
        #creating the async session 
        try:
            self.async_engine = create_async_engine(url=postgres_uri)
            self.async_session = async_sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        except Exception as error:
            raise error 

    #async function to retrieve the session
    async def get_db(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.async_session() as session:
            yield session

    #method to close connection to relational DB
    async def close_db(self):
        try:
            await self.async_engine.dispose() #closing connection to postgres server
        except Exception as error:
            raise error

#Cache
class CacheDatabase:
    def __init__(self, cache_url:str, cache_port:int, decode_responses=True):
        #initializing connection to cache database
        try:
            self.redis_db = Redis(
                host=cache_url,
                port=cache_port,
                decode_responses=decode_responses
            )
        except RedisError as error:
            raise error

    #CRUD methods for the cache 
    #Create
    async def insert(self, key:str, value:str, exp_time:int=600) -> None:
        try:
            await self.redis_db.set(key, value, ex=exp_time)
        except RedisError as error:
            raise error

    async def acquire_lock(self, key:str, token:str, exp_time:int=120) -> bool:
        try:
            return bool(await self.redis_db.set(key, token, ex=exp_time, nx=True))
        except RedisError as error:
            raise error

    async def release_lock(self, key:str, token:str):
        # Only the request that acquired the lock may release it.
        script = "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end"
        try:
            await self.redis_db.eval(script, 1, key, token)
        except RedisError as error:
            raise error

    #redis list insert 
    async def insert_list(self, key:str, value:str, exp_time:int=600) -> None:
        try:
            await self.redis_db.rpush(key, value) #inserting the item in the lst 

            #getting lst elements 
            redis_lst = await self.redis_db.lrange(key, 0, -1) #getting full range of the list
            if len(redis_lst) == 1:
                await self.redis_db.expire(key, time=exp_time)
        except RedisError as error:
            raise error   

    # Return the number of cached items without removing anything.
    async def list_length(self, key: str) -> int:
        try:
            return await self.redis_db.llen(key)
        except RedisError as error:
            raise error

    # Remove one exact item from the list after its payment is complete.
    async def remove_list_item(self, key: str, value: str, count: int = 1) -> int:
        try:
            return await self.redis_db.lrem(key, count, value)
        except RedisError as error:
            raise error

    # Read the full Redis list without consuming any of its items.
    async def retrieve_lst(self, key:str) -> list[str]:
        try:
            return await self.redis_db.lrange(key, 0, -1)
        except RedisError as error:
            raise error

    #Get
    async def retrieve(self, key:str) -> str | None:
        #retrieves the value in cache at key
        try:
            value = await self.redis_db.get(key)
            #if cache miss -> return None
            if not value:
                return None 

            return value #returns if cache hit
        except RedisError as error:
            raise error

    #Delete
    async def delete(self, key:str) -> None:
        #deletes the value at key in cache 
        try:
            await self.redis_db.delete(key) 
        except RedisError as error:
            raise error

    #method to close cache database
    async def close_cache(self):
        try:
            await self.redis_db.aclose() #closes connection to database
        except RedisError as error:
            raise error

#Vector
#Enum for the type of collection
class CollectionType(StrEnum):
    AGENT='agent'

#Wrapper for the Qdrant database
class VectorDatabase:
    def __init__(self, qdrant_url:str, 
                 qdrant_api_key:str, 
                 embedding_model:str,
                 agent_collection:str="agents"):
        #initializing the qdrant database
        try:
            self.vector_database = AsyncQdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key
            )
        except Exception as error:
            raise error 

        self.embedding_model = embedding_model #embedding model name
        self.agent_collection = agent_collection

    #helper method -> converts list of embedding to vector points
    @staticmethod
    def create_vector_points(embeddings:list) -> list:
        points_lst = [] #empty lst to store embeddings 

        #looping through embeddings creating points 
        for embedding_point in embeddings:
            embedding_id = str(uuid4()) #generating the id for the vector

            #initializing vector point
            point = PointStruct(
                id=embedding_id,
                vector=embedding_point
            )

            points_lst.append(point) #appending vector point to the lst

        return points_lst

    #static method to retrieve the Ids 
    @staticmethod
    def retrieve_point_ids(database_query):
        point_id_lst = [] #empty lst to store 

        #querying through the points -> appending to lst
        for point in database_query:
            point_id_lst.append(point.id) 

        return PointIdsList(
            points=point_id_lst
        ) #returns the lst of points 

    #helper method -> retrieves the collection name for collection type 
    def retrieve_collection_name(self, collection_type:CollectionType):
        #match case for type with name 
        match collection_type:
            case CollectionType.AGENT:
                return self.agent_collection

    #method runs in application startup -> configures the collection
    async def create_collection(self, collection_type:CollectionType, dimension_size:int=1024) -> None:
        collection_name = self.retrieve_collection_name(collection_type) #getting the name for collection

        #creating the collection
        try:
            if not await self.vector_database.collection_exists(collection_name):
                await self.vector_database.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=dimension_size, distance=Distance.COSINE)
                )
        except Exception as error:
            raise error

    #method to embed the text
    async def create_vector_embedding(self, 
                                      openai_client:AsyncClient, 
                                      text:str, 
                                      dimension_size:int=1024) -> list:
        #calling openai client to handle embedding text
        try:
            response = await openai_client.embeddings.create(
                input=text,
                model=self.embedding_model,
                dimensions=dimension_size
            )
            text_embeddings:list = response.data[0].embedding #retrieving the embedding 

            #creating the data to be stored in vector db
            return text_embeddings
        except Exception as error:
            raise error

    #Crud methods for the vector database
    async def insert(self, embeddings:list, 
                     payload:dict, collection_type) -> None:
        collection_name = self.retrieve_collection_name(collection_type) #getting name for collection inserting into 

        #getting the embeddings as points 
        vector_points = [
            PointStruct(id=str(uuid4()), vector=embedding, payload=payload)
            for embedding in embeddings
        ]

        #CRUD methods 
        #CREATE
        try:
            await self.vector_database.upsert(
                collection_name=collection_name,
                points=vector_points,
                wait=True
            )
        except Exception as error:
            raise error

        return vector_points

    #GET
    async def retrieve(self, embeddings:list, limit:int, collection_type:CollectionType):
        collection_name = self.retrieve_collection_name(collection_type) #getting the collection name

        #querying the collection
        try:
            database_query = await self.vector_database.query_points(
                collection_name=collection_name,
                query=embeddings,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )

            return database_query #returning query
        except Exception as error:
            raise error


    #GET #2 -> filters by ids
    async def retrieve_filter_ids(self, 
                                  embeddings:list, 
                                  limit:int, 
                                  collection_type:CollectionType,
                                  excluded_ids:list[str]):
        collection_name = self.retrieve_collection_name(collection_type) #getting name of collection

        #querying with filter of ids 
        try:
            database_query = await self.vector_database.query_points(
                collection_name=collection_name,
                query=embeddings,
                query_filter=Filter(
                    must_not=[
                        FieldCondition(
                            key='agent_id',
                            match=MatchAny(any=excluded_ids),
                        )
                    ]
                ),
                with_payload=True,
                with_vectors=False,
                limit=limit
            )

            return database_query #returning query
        except Exception as error:
            raise error

    #DELETE
    async def delete_embeddings(self, embeddings:list, collection_type:CollectionType):
        collection_name = self.retrieve_collection_name(collection_type)

        #retrieving the points -> deleting their IDs
        try:
            database_query = await self.retrieve(
                embeddings, 
                limit=1, 
                collection_type=CollectionType.AGENT
            )
            if not database_query.points:
                return

            #getting the ids for the points 
            points_id_lst = self.retrieve_point_ids(database_query.points)

            #deleting the points at the IDs
            await self.vector_database.delete(
                collection_name=collection_name,
                points_selector=points_id_lst
            )
        except Exception as error:
            raise error 

    #closing the vector database 
    async def close_db(self):
        try:
            await self.vector_database.close()
        except Exception as error:
            raise error
