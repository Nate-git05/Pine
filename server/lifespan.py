#File for the application's startup and shutdown lifecycle
from contextlib import asynccontextmanager
from fastapi import FastAPI
from redis.asyncio import RedisError
import aiohttp
from server.config.configuration import (
    PINENUMBER,
    POSTGRES_URI,
    CACHE_PORT,
    CACHE_URL,
    SERVER_SECRET_KEY,
    QDRANT_URL,
    QDRANT_API_KEY,
    JOB_WEBHOOK_URL,
    EMBEDDING_MODEL,
    STRIPE_API_KEY
)
from server.config.database import (
    RelationalDatabase,
    CacheDatabase,
    VectorDatabase,
    CollectionType
)
from server.config.apis import (
    APIWrapper,
    NotificationEvents,
    IncomingJobsEvents
)
from server.applications.customers.agent.customer_agent import PineAgent

#app's lifespan function -> configures the servers attributes at startup time
@asynccontextmanager
async def lifespan(app:FastAPI):
    """Starting the application's databases"""
    #configuring the servers relational database
    try:
        relational_database = RelationalDatabase(
            postgres_uri=POSTGRES_URI
        )
        app.state.relational_database = relational_database #setting the Postgres wrapper as state
    except Exception:
        raise RuntimeError('Unable to connect and bind the Postgres uri to the relational mapper.')

    #configuring app's state for cache
    try:
        cache_database = CacheDatabase(
            cache_url=CACHE_URL,
            cache_port=int(CACHE_PORT)
        )
        app.state.cache_database = cache_database
    except RedisError:
        raise RuntimeError('Unable to initialize the redis connection to the cache database')

    #configuring the app's state for the vector database
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

    #starting up the servers api wrapper -> wraps apis used across server
    api_wrapper = APIWrapper()
    app.state.api_wrapper = api_wrapper

    #configuring the servers events
    app.state.notifications_event = NotificationEvents()
    app.state.jobs_event = IncomingJobsEvents()

    #getting the server private attributes
    app.state.server_key = SERVER_SECRET_KEY
    app.state.server_number = PINENUMBER #adding the server's number to the app state
    app.state.job_webhook_url = JOB_WEBHOOK_URL
    app.state.stripe_api_key = STRIPE_API_KEY

    #configuring the app's http async object
    app.state.http_client = aiohttp.ClientSession()

    #configuring the server's agent 
    app.state.pine_agent = PineAgent(
        
    )

    yield #yields the application running

    #closing the app's connections
    try:
        await relational_database.close_db()
    except Exception:
        raise RuntimeError('Unable to close the Postgres connection.')

    #closing the cache database
    try:
        await cache_database.close_cache()
    except RedisError:
        raise RuntimeError('Unable to close the cache database.')

    #closing the vector database
    try:
        await vector_database.close_db()
    except Exception:
        raise RuntimeError('Unable to close the vector database')

    await app.state.http_client.close()
