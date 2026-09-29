#File for the webhook thats communicates directly to the client 
from fastapi.exceptions import HTTPException
from fastapi import Depends, Header
from fastapi.sse import EventSourceResponse
from server.applications.customers.routes.webhooks.apis.job_webhook import customer_api_webhook_router
from server.applications.customers.services.auth.auth_service import get_current_customer
from server.dependencies import (
    get_cache_db,
    get_server_key,
    get_jobs_events,
    get_relational_db_session
)
from server.models.users.customers import Customer
from server.models.activities.jobs.agent_job import (
    AgentJob,
    AgentJobState
)
from server.applications.customers.schemas.webhooks.webhook_schema import (
    ClientWebhook,
    CachedClientJob,
    AgentJobYield
)
from server.config.database import CacheDatabase
from server.config.apis import IncomingJobsEvents
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Annotated
from redis.asyncio import RedisError
import hmac
import hashlib
from uuid import uuid4
from server.applications.customers.services.pages.home_service import (
    get_pending_job_queue_key,
)

"""Route gets requests from agent/job/integrations webhook to send job over to client"""
@customer_api_webhook_router.post('/client')
async def send_cached_job(client_signature:Annotated[str, Header(alias='Signature')],
                          customer_info:ClientWebhook,
                          session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
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

    # The webhook's agent_id is the hired-agent row ID. Use it to check the
    # active job directly; the job table already records that relationship.
    cache_key = get_pending_job_queue_key(customer_info.customer_id, customer_info.agent_id)

    # Read the queue length without removing its first job.
    try:
        cached_job_count = await cache_db.list_length(cache_key)
        active_jobs_query = await session_db.execute(select(AgentJob).where(
            AgentJob.hired_agent_id == customer_info.agent_id,
            AgentJob.customer_id == customer_info.customer_id,
            AgentJob.job_state == AgentJobState.ACTIVE
        ))
        active_job = active_jobs_query.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Unable to check the agent job queue.'
        )

    # Add a stable offer ID so the client and payment route select this exact item.
    cached_offer = CachedClientJob(
        **customer_info.model_dump(),
        offer_id=uuid4(),
    )
    cached_job_value = cached_offer.model_dump_json()

    # Store every offer in the per-customer, per-agent queue.
    try:
        await cache_db.insert_list(
            key=cache_key,
            value=cached_job_value,
            exp_time=86400
        )
    except RedisError:
        try:
            await cache_db.remove_list_item(cache_key, cached_job_value)
        except RedisError:
            pass
        raise HTTPException(
            status_code=500,
            detail='Unable to operate on the cache.'
        )

    # Only announce an offer when no job is active and the queue was empty.
    if cached_job_count == 0 and not active_job:
        try:
            await server_events.event_set(
                data={
                    'customer_id': str(customer_info.customer_id),
                    'customer_data': cached_offer.model_dump(mode='json'),
                }
            )
        except Exception as error:
            raise HTTPException(
                status_code=500,
                detail='The offer was cached, but Pine could not publish it to the customer.'
            ) from error

        return {'response': 'The job offer was sent to the customer.', 'offer_id': str(cached_offer.offer_id)}

    return {'response': 'The job offer was queued until the agent is available.'}

"""Route for a server side event -> yields job created"""
@customer_api_webhook_router.get('/client/event')
async def stream_customer_job(customer:Annotated[Customer, Depends(get_current_customer)],
                              server_events:Annotated[IncomingJobsEvents, Depends(get_jobs_events)]):
    async def stream_jobs():
        while True:
            customer_id = str(customer.id)
            #waiting for an incoming job in this customer's queue
            await server_events.event_wait(customer_id)
            event_data = await server_events.get_item(customer_id)

            #checking the queued job belongs to the validated customer
            if not event_data or event_data.get('customer_id') != customer_id:
                continue

            customer_data = event_data.get('customer_data')
            if not isinstance(customer_data, dict):
                continue

            try:
                cached_job = CachedClientJob.model_validate(customer_data)
            except Exception:
                continue

            #sending the incoming job offer to the client
            yield AgentJobYield(
                offer_id=cached_job.offer_id,
                agent_name=cached_job.agent_name,
                agent_id=str(cached_job.agent_id),
                job_name=cached_job.job_name,
                job_description_str=cached_job.job_description,
                job_price=(cached_job.job_price / 100),
            )

    return EventSourceResponse(stream_jobs())
