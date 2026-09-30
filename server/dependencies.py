#File for the server dependency getter functions
from fastapi.requests import Request
from pydantic_extra_types.phone_numbers import PhoneNumber
from server.config.apis import APIWrapper
from server.config.database import (
    CacheDatabase,
    RelationalDatabase,
    VectorDatabase
)

#getting a relational database session
async def get_relational_db_session(request:Request):
    relational_database:RelationalDatabase = request.app.state.relational_database

    #looping through database to retrieve session
    async for session in relational_database.get_db():
        yield session

#getting the cache database
def get_cache_db(request:Request) -> CacheDatabase:
    return request.app.state.cache_database

#getting the vector database
def get_vector_database(request:Request) -> VectorDatabase:
    return request.app.state.vector_database

#getting the server's api clients
def get_twilio_client(request:Request):
    api_wrapper:APIWrapper = request.app.state.api_wrapper

    return api_wrapper.configure_twilio_api() #returns client

def get_openai_client(request:Request):
    api_wrapper:APIWrapper = request.app.state.api_wrapper

    return api_wrapper.configure_openai_api()

#getting the notification events
def get_notifications_events(request:Request):
    return request.app.state.notifications_event

#getting the incoming job events
def get_jobs_events(request:Request):
    return request.app.state.jobs_event

#getting the server's secret key
def get_server_key(request:Request):
    return request.app.state.server_key

#getting the server's number
def get_servers_number(request:Request):
    return PhoneNumber(request.app.state.server_number)

#getting the server's async client for http requests
async def get_async_http(request:Request):
    return request.app.state.http_client

#getting Pine's client webhook URL
def get_client_webhook_url(request:Request) -> str:
    return request.app.state.client_webhook_url

#getting Stripe's api key
def get_stripe_api_key(request:Request):
    return request.app.state.stripe_api_key

"""getting the server\'s agent"""
def get_server_agent(request:Request):
    return request.app.state.pine_agent
