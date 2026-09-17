#Database configuration file for the server
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from typing import AsyncGenerator


"""Configuring databases for the server"""
#Relational 
class RelationalDatabase:
    def __init__(self, postgres_uri:str):
        #creating the async session 
        try:
            async_engine = create_async_engine(url=postgres_uri)
            self.async_session = async_sessionmaker(
                bind=async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        except Exception as error:
            raise error 

    #async function to retrieve the session
    async def get_db(self):
        async with self.async_session() as session:
            yield session