#File for the webhook thats communicates directly to the client 
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.applications.customers.routes.webhooks.apis.job_webhook import customer_api_webhook_router
from server.applications.customers.services.auth.auth_service import get_current_customer
from server.app import (
    get_cache_db,
    get_server_key
)
from server.models.users.customers import Customer
from server.applications.customers.schemas.webhooks.webhook_schema import (
    ClientWebhook,
    AgentJobYield
)
from server.config.database import CacheDatabase
from typing import Annotated
from redis.asyncio import RedisError
import hmac
import hashlib

"""Route gets requests from agent/job/integrations webhook to send job over to client"""
@customer_api_webhook_router.post('/client')
async def send_cached_job(client_signature:Annotated[str, Depends()],
                          customer_info:ClientWebhook,
                          pine_server_key:Annotated[str, Depends(get_server_key)],
                          cache_db:Annotated[CacheDatabase, Depends(get_cache_db)]):
    #getting the signature 
    signature = hmac.new(
        pine_server_key.encode('utf-8'),
        customer_info.model_dump_json(),
        digestmod=hashlib.sha256()
    )

    #checking the client signature 
    if not hmac.compare_digest(
        signature,
        client_signature
    ):
        raise HTTPException(
            status_code=400,
            detail='Invalid signature. Request failed.'
        )

    #storing the request in the cache 
    cache_key = str(customer_info.customer_id)
    try:
        await cache_db.insert(
            key=cache_key,
            value=customer_info.model_dump_json()
        )
    except RedisError:
        raise HTTPException(
            status_code=500,
            detail='Unable to operate on the cache.'
        )

    return customer_info #returning the customer info to the client

"""Route for a server side event -> yields job created"""
@customer_api_webhook_router.get('/client/event')
async def stream_customer_job(customer_id:Annotated[Customer, Depends(get_current_customer)]):
    async def get_customer_job():
        