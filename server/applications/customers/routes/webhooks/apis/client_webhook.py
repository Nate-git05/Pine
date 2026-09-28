#File for the webhook thats communicates directly to the client 
from fastapi.exceptions import HTTPException
from fastapi import Depends, Header
from fastapi.sse import EventSourceResponse
from server.applications.customers.routes.webhooks.apis.job_webhook import customer_api_webhook_router
from server.applications.customers.services.auth.auth_service import get_current_customer
from server.app import (
    get_cache_db,
    get_server_key,
    get_jobs_events
)
from server.models.users.customers import Customer
from server.applications.customers.schemas.webhooks.webhook_schema import (
    ClientWebhook,
    AgentJobYield
)
from server.config.database import CacheDatabase
from server.config.apis import IncomingJobsEvents
from typing import Annotated
import json
from redis.asyncio import RedisError
import hmac
import hashlib

"""Route gets requests from agent/job/integrations webhook to send job over to client"""
@customer_api_webhook_router.post('/client')
async def send_cached_job(client_signature:Annotated[str, Header(alias='Signature')],
                          customer_info:ClientWebhook,
                          pine_server_key:Annotated[str, Depends(get_server_key)],
                          cache_db:Annotated[CacheDatabase, Depends(get_cache_db)],
                          server_events:Annotated[IncomingJobsEvents, Depends(get_jobs_events)]):
    #getting the signature 
    signature = hmac.new(
        pine_server_key.encode('utf-8'),
        customer_info.model_dump_json().encode('utf-8'),
        digestmod=hashlib.sha256
    )

    #checking the client signature 
    if not hmac.compare_digest(
        signature.hexdigest(),
        client_signature
    ):
        raise HTTPException(
            status_code=400,
            detail='Invalid signature. Request failed.'
        )

    #storing the request in the cache 
    cache_key = f'{str(customer_info.customer_id)}/{customer_info.agent_name}'
    try:
        await cache_db.insert_list(
            key=cache_key,
            value=customer_info.model_dump_json(),
            exp_time=900
        )
    except RedisError:
        raise HTTPException(
            status_code=500,
            detail='Unable to operate on the cache.'
        )

    #setting the event to set for the customer cached job 
    try:
        await server_events.event_set(
            data={
                'customer_id':str(customer_info.customer_id),
                'customer_data':customer_info.model_dump(mode='json')
            }
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Unable to authenticate this client webhook request.'
        )

"""Route for a server side event -> yields job created"""
@customer_api_webhook_router.get('/client/event')
async def stream_customer_job(customer:Annotated[Customer, Depends(get_current_customer)],
                              server_events:Annotated[IncomingJobsEvents, Depends(get_jobs_events)]):
    async def stream_jobs():
        while True:
            customer_id = str(customer.id)
            await server_events.event_wait(customer_id)
            event_data = await server_events.get_item(customer_id)
            customer_data = event_data.get('customer_data') or {}
            yield AgentJobYield(
                agent_name=customer_data.get('agent_name'),
                agent_id=customer_data.get('agent_id'),
                job_name=customer_data.get('job_name'),
                job_description_str=customer_data.get('job_description'),
                job_price=(customer_data.get('job_price') / 100)
            )

    return EventSourceResponse(stream_jobs())
