#File for starting up the application for the server
from fastapi import FastAPI
from fastapi.requests import Request
from server.config.configuration import (
    PINENUMBER,
    POSTGRES_URI,
    CACHE_PORT,
    CACHE_URL,
    SERVER_SECRET_KEY,
    QDRANT_URL,
    QDRANT_API_KEY,
    OPENAI_API_KEY,
    EMBEDDING_MODEL
)
from server.config.database import (
    RelationalDatabase,
    CacheDatabase,
    VectorDatabase,
    CollectionType
)
from server.config.apis import (
    APIWrapper,
    NotificationEvents
)
from contextlib import asynccontextmanager
from pydantic_extra_types.phone_numbers import PhoneNumber
import aiohttp
from redis.asyncio import RedisError

#getter functions for retrieving app states
async def get_relational_db_session(request:Request):
    relational_database:RelationalDatabase = request.app.state.relational_database

    #looping through database to retriev session
    async for session in relational_database.get_db():
        yield session

def get_cache_db(request:Request):
    return request.app.state.cache_database

def get_vector_database(request:Request):
    return request.app.state.vector_database

#getting the server's api clients 
def get_twilio_client(request:Request):
    api_wrapper:APIWrapper = request.app.state.api_wrapper

    return api_wrapper.configure_twilio_api() #returns client

def get_openai_client(request:Request):
    api_wrapper:APIWrapper = request.app.state.api_wrapper

    return api_wrapper.configure_openai_api(
        api_key=OPENAI_API_KEY
    )

def get_notifications_events(request:Request):
    return request.app.state.notifications_event

#getting the server's secret key
def get_server_key(request:Request):
    return request.app.state.server_key

#getting the server's number 
def get_servers_number(request:Request):
    return PhoneNumber(request.app.state.server_number)

#getting the server's async client for http requests 
async def get_async_http(request:Request):
    return request.app.state.http_client

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

    #Configuring the app's state for the vector database
    try:
        vector_database = VectorDatabase(
            qdrant_url=QDRANT_URL,
            qdrant_api_key=QDRANT_API_KEY,
            embedding_model=EMBEDDING_MODEL,
        )
        app.state.vector_database = vector_database #apps state set to vector database

        #configuring the agent collection
        await vector_database.create_collection(
            collection_type=CollectionType.AGENT
        )
    except Exception:
        raise RuntimeError('Unable to configure the Qdrant connection for the vector database.')
    
    #Starting up the servers api wrapper -> wraps apis used across server
    api_wrapper = APIWrapper()
    app.state.api_wrapper = api_wrapper

    #configuring the servers notification events 
    app.state.notifications_event = NotificationEvents()

    #Getting the server private attributes 
    app.state.server_key = SERVER_SECRET_KEY
    app.state.server_number = PINENUMBER #adding the server's number to the app state

    #Configuring the app's http async object 
    app.state.http_client = aiohttp.ClientSession()

    yield #yields the application running 

    #Closing the aopen connections 
    try:
        await relational_database.close_db()
    except Exception:
        raise RuntimeError('Unable to close the Postgres connection.')

    #cache database
    try:
        await cache_database.close_cache()
    except RedisError:
        raise RuntimeError('Unable to close the cache database.')

    #vector database
    try:
        await vector_database.close_db()
    except Exception:
        raise RuntimeError('Unable to close the vector database')


#Initialzing the app 
app = FastAPI(lifespan=lifespan)