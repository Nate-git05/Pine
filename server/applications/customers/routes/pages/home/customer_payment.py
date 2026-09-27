#File for the routes for the customers payments 
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.applications.customers.routes.pages.home.agent_chat import customer_home_router
from server.app import (
    get_relational_db_session,
    get_stripe_api_key,
    get_cache_db,
    get_async_http,
    get_server_key,
    get_notifications_events
)
from server.applications.customers.services.auth.auth_service import get_current_customer
from server.models.users.customers import Customer
from server.models.agents.agent import Agent
from server.models.integrations.stripe_payments.stripe_payment import StripePayment
from server.models.notifications.notification_message import (
    Notification,
    NotificationState,
    NotificationType
)
from server.applications.customers.schemas.pages.home_schemas import (
    ReturnedPaymentsList,
    AgentsJobRequest
)
from server.applications.customers.services.pages.home_service import (
    get_returned_payments_lst,
    customer_payment_for_job,
    create_agents_new_job,
    get_hired_agent_url
)
from server.config.database import CacheDatabase
from server.config.apis import NotificationEvents
from sqlalchemy import select, and_ 
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Annotated
from aiohttp import ClientSession
from datetime import datetime, timezone
import hmac 
import hashlib
import json

"""Route for the customer to pay for the job"""
@customer_home_router.get('/cards', response_model=ReturnedPaymentsList)
async def get_customer_cards(customer:Annotated[Customer, Depends(get_current_customer)],
                             stripe_api_key:Annotated[str, Depends(get_stripe_api_key)],
                             session_db:Annotated[AsyncSession, Depends(get_relational_db_session)]):
    #database query for the customers payments
    try:
        customer_payments_query = await session_db.execute(select(StripePayment).where(
            StripePayment.customer_id == customer.id
        ))
        customer_payments = customer_payments_query.scalars().all()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Database error. Please attempt to pay again.'
        )

    #check if the customer has any connected payments 
    if not customer_payments:
        ReturnedPaymentsList(
            response='There aren\'t any connected payments.',
            payments_lst=None
        )

    #getting pydantic lst of payments
    try:
        payments_lst = get_returned_payments_lst(
            customer_payments,
            stripe_api_key
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail='API error. Unable to call the Stripe API.'
        )

    #returning lst to the client
    return ReturnedPaymentsList(
        response=None,
        payments_lst=payments_lst
    )

"""Route for the customer to pay with selected card"""
@customer_home_router.post('/payment/{payment_id_str}')
async def customer_job_payment(payment_id_str:str,
                               customer:Annotated[Customer, Depends(get_current_customer)], 
                               session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                               cache_db:Annotated[CacheDatabase, Depends(get_cache_db)],
                               stripe_api_key:Annotated[str, Depends(get_stripe_api_key)],
                               http_client:Annotated[ClientSession, Depends(get_async_http)],
                               pine_server_key:Annotated[str, Depends(get_server_key)],
                               notification_events:Annotated[NotificationEvents, Depends(get_notifications_events)]):
    #casting payment id str -> uuid
    try:
        payment_id = UUID(payment_id_str)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=''
        )
    
    #database query for the customers payment 
    try:
        customer_payment_query = await session_db.execute(select(StripePayment).where(and_(
            StripePayment.id == payment_id,
            StripePayment.customer_id == customer.id
        )))
        customer_payment = customer_payment_query.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=''
        )

    #check if query returned None
    if not customer_payment:
        raise HTTPException(
            status_code=400,
            detail=''
        )

    #getting the cached job 
    try:
        cached_job = await cache_db.retrieve_lst(
            key=str(customer.id)
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=''
        )

    #check if cache miss 
    if not cached_job:
        raise HTTPException(
            status_code=400,
            detail=''
        )

    cached_job_dict = json.loads(cached_job) #loads in the cached job str as dict

    #calling stripe api for payments 
    try:
        payment_success = customer_payment_for_job(
            cached_job=cached_job_dict,
            customer_payment=customer_payment,
            stripe_api_key=stripe_api_key
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=''
        )

    #check if the payment was successful
    if not payment_success.status == "succeded":
        raise HTTPException(
            status_code=400,
            detail=f'There was an error in the payment. {payment_success.status}'
        )
    
    #getting the agents new job
    try:
        agent_job = await create_agents_new_job(
            session_db,
            customer,
            cached_job_dict
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=''
        )

    #creating the pydantic model for the agents job request 
    agent_job_model = AgentsJobRequest(
        customer_id=str(customer.id),
        job_id=str(agent_job.id),
        job_name=agent_job.job_name,
        job_description=agent_job.job_description
    )

    #getting signature for the request
    pine_siganture = hmac.new(
        pine_server_key.encode('utf-8'),
        agent_job_model.model_dump_json().encode('utf-8'),
        digestmod=hashlib.sha256()
    )

    #building out params for request
    headers = {
        'Signature':pine_siganture
    }
    data = agent_job_model.model_dump_json()
    #getting the agents url for request
    try:
        agent:Agent = await get_hired_agent_url()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=''
        )

    #sending the request to the hired agent
    try:
        async with http_client.post(
            url=agent.agents_webhook_url,
            headers=headers,
            data=data
        ) as response:
            #checking the status code of the response 
            if response.status >= 300 or response.status < 200:
                raise HTTPException(
                    status_code=400,
                    detail=''
                )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=''
        )

    #creating the notification for the customer 
    customer_notification = Notification(
        notification_header=f'Your agent {agent_job.hired_agent_name} has just been sent a job',
        notification_message=f'Agent {agent_job.hired_agent_name} has just been sent the job {agent_job.job_name}.',
        notification_type=NotificationType.JOB_ACTION,
        notification_state=NotificationState.UNREAD,
        customer_id=customer.id,
        created_at=datetime.now(timezone.utc)
    )

    merchant_notification = Notification(
        notification_header=f'New Payment Incoming.',
        notification_message=f'Your agent {agent.name} has just been given a job.',
        notification_type=NotificationType.JOB_ACTION,
        notification_state=NotificationState.UNREAD,
        merchant_id=agent.merchant_id,
        created_at=datetime.now(timezone.utc)
    )

    #staging and commit the agent and customers noti
    try:
        session_db.add(customer_notification)
        session_db.add(merchant_notification)
        await session_db.flush()
        await session_db.commit()
    except Exception:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail=''
        )

    #setting the event for customer to get phone notification
    try:
        notification_events.event_set(
            data={
                'customer_id':str(customer.id),
                'customer_noti': {
                    'noti_id':str(customer_notification.id),
                    'noti_header':customer_notification.notification_header,
                    'noti_message':customer_notification.notification_message
                }
            }
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=''
        )

"""Route for the customer to add a card"""
@customer_home_router.post('/add')
async def add_customer_payment():
    pass