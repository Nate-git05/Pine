#File for the webhook thats communicates directly to the client 
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.applications.customers.routes.webhooks.apis.job_webhook import customer_api_webhook_router
from server.applications.customers.services.auth.auth_service import get_current_customer
from server.app import (
    get_cache_db,
    get_server_key,
    get_server_events
)
from server.models.users.customers import Customer
from server.applications.customers.schemas.webhooks.webhook_schema import (
    ClientWebhook,
    AgentJobYield
)
from server.config.database import CacheDatabase
from server.config.apis import ServerEvents
from typing import Annotated
import json
from redis.asyncio import RedisError
import hmac
import hashlib

"""Route gets requests from agent/job/integrations webhook to send job over to client"""
@customer_api_webhook_router.post('/client')
async def send_cached_job(client_signature:Annotated[str, Depends()],
                          customer_info:ClientWebhook,
                          pine_server_key:Annotated[str, Depends(get_server_key)],
                          cache_db:Annotated[CacheDatabase, Depends(get_cache_db)],
                          server_events:Annotated[ServerEvents, Depends(get_server_events)]):
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

    #setting the event to set for the customer cached job 
    try:
        await server_events.event_set(
            data=json.loads(
                customer_info.model_dump_json()
            )
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=''
        )

"""Route for a server side event -> yields job created"""
@customer_api_webhook_router.get('/client/event')
async def stream_customer_job(customer_id:Annotated[Customer, Depends(get_current_customer)],
                              server_events:Annotated[ServerEvents, Depends(get_server_events)]):
    async def get_customer_job() -> dict:
        while not server_events.async_queue:
            server_events.event_wait()

        #event is now set 
        try:
            customer_data:dict = server_events.get_item()
            return customer_data 
        except Exception as err:
            raise err

    #getting the customer data from inner fucntion
    try:
        customer_data:dict = await get_customer_job()
        if not customer_data:
            raise Exception('Unable to locate the item in queue.')
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=''
        )

    #pydantic model for cached job 
    cached_job = AgentJobYield(
        agent_name=customer_data.get('agent_name'),
        job_name=customer_data.get('job_name'),
        job_description_str=customer_data.get('job_description'),
        job_price=customer_data.get('job_price')
    )

    #yielding to the client
    yield cached_job