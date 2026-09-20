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
    PointStruct
)
from openai import AsyncClient
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
            self.redis_db =  Redis(
                host=cache_url,
                port=cache_port,
                decode_responses=decode_responses
            )
        except RedisError as error:
            raise error

    #CRUD methods for the cache 
    #Create
    async def insert(self, key:str, value:str, exp_time:int=600):
        try:
            await self.redis_db.set(key, value, ex=exp_time)
        except RedisError as error:
            raise error

    #Get
    async def retrieve(self, key:str):
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
    async def delete(self, key:str):
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
                 agent_collection:str):
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
        for embedding_id, embedding_point in enumerate(embeddings):
            #initializing vector point
            point = PointStruct(
                id=embedding_id,
                vector=embedding_point
            )

            points_lst.append(point) #appending vector point to the lst

        return points_lst

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
        vector_points = self.create_vector_points(
            embeddings=embeddings
        )

        #inserting the vectors into the database
        try:
            await self.vector_database.upsert(
                collection_name=self.agent_collection,
                points=vector_points,
                payload=payload
            )
        except Exception as error:
            raise error

    #retrieving points from vector 
    async def retrieve(self, embeddings:list, limit:int, collection_type:CollectionType):
        collection_name = self.retrieve_collection_name(collection_type) #getting the collection name

        #querying the collection
        try:
            database_query = await self.vector_database.query_points(
                collection_name=collection_name,
                query=embeddings,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
        except Exception as error:
            raise error

        payload_lst = [query.payload for query in database_query.points if query.payload] #list to store the payloads 
        return payload_lst
