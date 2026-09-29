#File for starting up the application for the server
from fastapi import FastAPI
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
from contextlib import asynccontextmanager
import aiohttp
from redis.asyncio import RedisError

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

    #configuring the servers events 
    app.state.notifications_event = NotificationEvents()
    app.state.jobs_event = IncomingJobsEvents()

    #Getting the server private attributes 
    app.state.server_key = SERVER_SECRET_KEY
    app.state.server_number = PINENUMBER #adding the server's number to the app state
    app.state.job_webhook_url = JOB_WEBHOOK_URL
    app.state.stripe_api_key = STRIPE_API_KEY

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
    await app.state.http_client.close()


#Initialzing the app 
app = FastAPI(lifespan=lifespan)

# Register customer routes after creating the app to avoid import cycles.
from server.applications.customers.routes.auth.signup import customer_auth_router
from server.applications.customers.routes.auth import login as _customer_login_routes
from server.applications.customers.routes.auth import verify as _customer_verify_routes
from server.applications.customers.routes.pages.home.customer_payment import customer_home_router
from server.applications.customers.routes.pages.search.agent_search import customer_search_router
from server.applications.customers.routes.pages.search import hire_agent as _customer_hire_routes
from server.applications.customers.routes.pages.activity.rest.customer_jobs import customer_activity_router as customer_jobs_router
from server.applications.customers.routes.pages.activity.rest.customer_requests import customer_activity_router as customer_requests_router
from server.applications.customers.routes.pages.home.notifications.notifications_sse import customer_sse_router
from server.applications.customers.routes.pages.home.notifications.graphql.notifications_page import notifications_page_router
from server.applications.customers.routes.pages.home.notifications.rest.notification_routes import customer_notification_router
from server.applications.customers.routes.webhooks.apis.job_webhook import customer_api_webhook_router
from server.applications.customers.routes.webhooks.apis import client_webhook as _client_webhook_routes
from server.applications.customers.routes.webhooks.apis import request_webhook as _request_webhook_routes
from server.applications.customers.routes.pages.activity.graphql.activity_page import activity_page_graphql_router

for router in (
    customer_auth_router, customer_home_router, customer_search_router,
    customer_jobs_router, customer_requests_router, customer_sse_router,
    customer_notification_router, notifications_page_router,
    customer_api_webhook_router, activity_page_graphql_router,
):
    app.include_router(router)
