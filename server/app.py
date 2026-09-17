#File for starting up the application for the server
from fastapi import FastAPI
from fastapi.requests import Request
from server.config.configuration import (
    PINENUMBER,
    POSTGRES_URI,
    CACHE_PORT,
    CACHE_URL
)
from server.config.database import (
    RelationalDatabase,
    CacheDatabase
)
from server.config.apis import APIWrapper
from contextlib import asynccontextmanager
from redis.asyncio import RedisError

#getter functions for retrieving app states
async def get_relational_db_session(request:Request):
    relational_database:RelationalDatabase = request.app.state.relational_database

    #looping through database to retriev session
    async for session in relational_database.get_db():
        yield session
        break #yields only one session

def get_cache_db(request:Request):
    return request.app.state.cache_database

#getting the twilio client
def get_twilio_client(request:Request):
    api_wrapper:APIWrapper = request.app.state.api_wrapper

    return api_wrapper.configure_twilio_api() #returns client

#getting the server's number 
def get_servers_number(request:Request):
    return request.app.state.server_number

#app's lifespan function -> configures the servers attributes at startup time
@asynccontextmanager
async def lifespan(app:FastAPI):
    """Starting the application's databases"""
    #configuring the servers relational database
    try:
        relational_database = RelationalDatabase(
            postgres_uri=POSTGRES_URI
        )
        app.state.relational_datbase = relational_database #setting the POstgres wrapper as state 
    except Exception:
        raise RuntimeError('Unable to connect and bind the Postgres uri to the relational mapper.')
    
    #configuring app's state for cache 
    try:
        cache_database = CacheDatabase(
            cache_url=CACHE_URL,
            cache_port=CACHE_PORT
        )
        app.state.cache_database = cache_database
    except RedisError:
        raise RuntimeError('Unable to initialize the redis connection to the cache database')

    #Starting up the servers api wrapper -> wraps apis used across server
    api_wrapper = APIWrapper()
    app.state.api_wrapper = api_wrapper

    app.state.server_number = PINENUMBER #adding the server's number to the app state

    yield #yields the application running 


#Initialzing the app 
app = FastAPI(lifespan=lifespan)