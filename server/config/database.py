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
class VectorDatabase:
    def __init__(self, url:str, api_key:str, model_name:str):
        #initializing the qdrant database
        try:
            self.vector_database = AsyncQdrantClient(
                url=url,
                api_key=api_key
            )
        except Exception as error:
            raise error 

        #configuring the embedding model 
        