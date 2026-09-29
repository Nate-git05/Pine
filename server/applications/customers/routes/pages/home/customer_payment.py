#File for the routes for the customers payments 
from fastapi.requests import Request
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.applications.customers.routes.pages.home.agent_chat import customer_home_router
from server.dependencies import (
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
    AgentsJobRequest,
    PaymentResponse,
    StripePaymentResponse
)
from server.applications.customers.services.pages.home_service import (
    get_returned_payments_lst,
    customer_payment_for_job,
    create_agents_new_job,
    get_hired_agent_url,
    create_new_job_payment
)
from server.config.database import CacheDatabase
from server.config.apis import NotificationEvents
from sqlalchemy import select, and_ 
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, uuid4
from typing import Annotated, AsyncGenerator
from aiohttp import ClientSession
from datetime import datetime, timezone
import stripe
import hmac 
import hashlib
import json


async def lock_payment_offer(
    offer_id_str:str,
    customer:Annotated[Customer, Depends(get_current_customer)],
    cache_db:Annotated[CacheDatabase, Depends(get_cache_db)]
) -> AsyncGenerator[None, None]:
    try:
        offer_id = UUID(offer_id_str)
    except ValueError as error:
        raise HTTPException(status_code=400, detail='Invalid job offer.') from error
    lock_key = f'payment-lock/{customer.id}/{offer_id}'
    lock_token = str(uuid4())
    if not await cache_db.acquire_lock(lock_key, lock_token):
        raise HTTPException(status_code=409, detail='This job offer is already being processed.')
    try:
        yield
    finally:
        try:
            await cache_db.release_lock(lock_key, lock_token)
        except Exception:
            # The lock has a short expiry, so a Redis outage cannot leave it permanent.
            pass

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
        return ReturnedPaymentsList(
            response='There aren\'t any connected payments.',
            payments_lst=[]
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
@customer_home_router.post('/payment/{payment_id_str}/{offer_id_str}', response_model=PaymentResponse)
async def customer_job_payment(payment_id_str:str,
                               offer_id_str:str,
                               customer:Annotated[Customer, Depends(get_current_customer)], 
                               session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                               cache_db:Annotated[CacheDatabase, Depends(get_cache_db)],
                               stripe_api_key:Annotated[str, Depends(get_stripe_api_key)],
                               http_client:Annotated[ClientSession, Depends(get_async_http)],
                               pine_server_key:Annotated[str, Depends(get_server_key)],
                               notification_events:Annotated[NotificationEvents, Depends(get_notifications_events)],
                               _payment_offer_lock:Annotated[None, Depends(lock_payment_offer)]):
    #casting payment id str -> uuid
    try:
        payment_id = UUID(payment_id_str)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail='Invalid payment id. Please select a saved card and try again.'
        )

    try:
        offer_id = UUID(offer_id_str)
    except ValueError as error:
        raise HTTPException(status_code=400, detail='Invalid job offer. Please select the offer again.') from error

    processed_offer_key = f'paid-job-offer/{customer.id}/{offer_id}'
    if await cache_db.retrieve(key=processed_offer_key):
        return PaymentResponse(response='This offer was already paid. Check activity for its status before retrying.')
    
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
            detail='Unable to look up the saved payment method. Please try again.'
        )

    #check if query returned None
    if not customer_payment:
        raise HTTPException(
            status_code=400,
            detail='That saved payment method was not found for your account.'
        )

    #getting the cached job 
    try:
        cached_job = await cache_db.retrieve(key=f'pending-job/{customer.id}/{offer_id}')
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Unable to retrieve the pending job. Please submit the job again.'
        )

    #check if cache miss 
    if not cached_job:
        raise HTTPException(
            status_code=400,
            detail='Unable to process the payment. Check your payment method and try again.'
        )

    cached_job_dict = json.loads(cached_job) #loads in the cached job str as dict
    if cached_job_dict.get('offer_id') != str(offer_id) or cached_job_dict.get('customer_id') != str(customer.id):
        raise HTTPException(status_code=400, detail='This job offer is invalid or has expired.')

    #Validate the offer and customer-agent relationship before charging the card.
    try:
        offered_agent_id = UUID(cached_job_dict.get('agent_id'))
        offered_price = cached_job_dict.get('job_price')
        if not isinstance(offered_price, int) or offered_price <= 0:
            raise ValueError('The offer price must be a positive amount in cents.')
        hired_agent_query = await session_db.execute(select(HiredAgent).where(and_(
            HiredAgent.agent_id == offered_agent_id,
            HiredAgent.customer_id == customer.id,
            HiredAgent.agent_state == 'active'
        )))
        if not hired_agent_query.scalar_one_or_none():
            raise ValueError('This offer is not from an active agent hired by this customer.')
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail='This job offer is invalid or is not from an active hired agent.'
        ) from error

    #calling stripe api for payments 
    try:
        payment_success = customer_payment_for_job(
            cached_job=cached_job_dict,
            customer_payment=customer_payment,
            stripe_api_key=stripe_api_key,
            idempotency_key='pine-' + hashlib.sha256(
                f'{customer.id}:{offer_id}:{customer_payment.stripe_payment_id}'.encode('utf-8')
            ).hexdigest()
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Unable to process the payment. Please try again.'
        )

    #check if the payment was successful
    if payment_success.status != "succeeded":
        raise HTTPException(
            status_code=400,
            detail=f'There was an error in the payment. {payment_success.status}'
        )
    customer_payment.last_used = datetime.now(timezone.utc) #updating attribute
    
    try:
        agent_job = await create_agents_new_job(
            session_db,
            customer,
            cached_job_dict
        )
        await create_new_job_payment(
            session_db,
            agent_job
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Payment was processed, but Pine could not save the job. Contact support before retrying to avoid a duplicate charge.'
        )

    try:
        await cache_db.insert(
            key=processed_offer_key,
            value=str(agent_job.id),
            exp_time=86400
        )
    except Exception as error:
        try:
            await cache_db.delete(key=f'pending-job/{customer.id}/{offer_id}')
        except Exception:
            pass
        raise HTTPException(
            status_code=500,
            detail='Payment and job were saved, but Pine could not record the offer result. Check activity before retrying.'
        ) from error

    # Keep declined offers available; consume successful offers after durable records exist.
    try:
        await cache_db.delete(key=f'pending-job/{customer.id}/{offer_id}')
    except Exception:
        # Stripe's idempotency key protects the charge if Redis is unavailable.
        pass

    #getting the agents url for request
    try:
        hired_agent_query = await session_db.execute(select(HiredAgent).where(and_(
            HiredAgent.id == agent_job.hired_agent_id,
            HiredAgent.customer_id == customer.id,
            HiredAgent.agent_state == 'active'
        )))
        hired_agent = hired_agent_query.scalar_one_or_none()
        if not hired_agent:
            raise ValueError('Hired agent not found for this customer.')
        agent:Agent = await get_hired_agent_url(session_db, hired_agent)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Unable to locate the hired agent endpoint.'
        )

    #creating the pydantic model for the agents job request
    agent_job_model = AgentsJobRequest(
        customer_id=str(customer.id),
        job_id=str(agent_job.id),
        job_name=agent_job.job_name,
        job_description=agent_job.job_description,
        agent_restrictions=hired_agent.agent_restrictions
    )

    #getting signature for the request
    pine_siganture = hmac.new(
        pine_server_key.encode('utf-8'),
        agent_job_model.model_dump_json().encode('utf-8'),
        digestmod=hashlib.sha256
    )

    #building out params for request
    headers = {
        'Content-type':'application/json',
        'Signature':pine_siganture.hexdigest()
    }
    data = agent_job_model.model_dump_json()

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
                    detail='The agent endpoint did not accept the job. Check job activity before retrying.'
                )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Unable to send the job to the agent. Check job activity before retrying.'
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
            detail='Payment completed, but Pine could not save the notification. Refresh your activity to check the job status.'
        )

    #setting the event for customer to get phone notification
    try:
        await notification_events.event_set(
            data={
                'customer_id':str(customer.id),
                'customer_noti': {
                    'noti_id':str(customer_notification.id),
                    'noti_header':customer_notification.notification_header,
                    'noti_message':customer_notification.notification_message,
                    'noti_type':customer_notification.notification_type
                }
            }
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Payment completed, but Pine could not publish the notification. Refresh your notifications.'
        )

    #returning success to the client 
    return PaymentResponse(
        response='Payment succeded. Agent is now beginning job.'
    )

"""Route for the customer to add a card"""
@customer_home_router.post('/payment/add')
async def add_customer_payment(customer:Annotated[Customer, Depends(get_current_customer)],
                               cache_db:Annotated[CacheDatabase, Depends(get_cache_db)],
                               stripe_api_key:Annotated[str, Depends(get_stripe_api_key)],
                               session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                               request:Request):
    existing_payment_query = await session_db.execute(select(StripePayment.stripe_customer_id).where(
        StripePayment.customer_id == customer.id
    ).limit(1))
    customer_stripe_id = existing_payment_query.scalar_one_or_none()
    cache_key = f'{str(customer.id)}/stripe'
    if not customer_stripe_id:
        pending_setup = await cache_db.retrieve(key=cache_key)
        if pending_setup:
            try:
                customer_stripe_id = json.loads(pending_setup).get('customer_stripe_id')
            except (TypeError, json.JSONDecodeError):
                customer_stripe_id = None
    if not customer_stripe_id:
        try:
            customer_stripe = stripe.Customer.create(
                api_key=stripe_api_key,
                email=str(customer.email),
                name=customer.name
            )
            customer_stripe_id = customer_stripe.id
        except Exception as error:
            raise HTTPException(
                status_code=400,
                detail='Unable to create a Stripe customer for card setup. Please try again.'
            ) from error

    #caching the customer's payment 
    try:
        data = json.dumps({
            'customer_stripe_id':customer_stripe_id,
        })
        await cache_db.insert(cache_key, data)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Unable to save card setup details. Please try again.'
        )

    #creating customers stripe session -> stripe to create payment id
    try:
        stripe_session = stripe.checkout.Session.create(
            api_key=stripe_api_key,
            mode='setup',
            customer=customer_stripe_id,
            success_url=(
                f'{request.url_for("created_payment_model")}'
                f'?session_id={{CHECKOUT_SESSION_ID}}&customer_id={customer.id}'
            ),
            cancel_url=(
                f'{request.url_for("payment_creation_failed")}'
                f'?customer_id={customer.id}'
            )
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail='Unable to start secure card setup. Please try again.'
        )

    return stripe_session.url #returning the url for customer to enter card info

"""Success and failed urls for Stripe"""
#success route 
@customer_home_router.get('/payment/add/success', response_model=StripePaymentResponse)
async def created_payment_model(request:Request,
                                session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                                cache_db:Annotated[CacheDatabase, Depends(get_cache_db)]):
    try:
        customer_id = UUID(request.query_params.get('customer_id', ''))
        cache_key = f'{str(customer_id)}/stripe'
        cached_setup = await cache_db.retrieve(key=cache_key)
        if not cached_setup:
            raise ValueError('Pending Stripe customer data is missing.')
        cache_data:dict = json.loads(cached_setup)
        if not cache_data or not cache_data.get('customer_stripe_id'):
            raise ValueError('Pending Stripe customer data is missing.')

        customer_query = await session_db.execute(select(Customer).where(Customer.id == customer_id))
        customer = customer_query.scalar_one_or_none()
        if not customer:
            raise ValueError('Customer account was not found.')

        #getting customer's stripe session
        query_param_session = request.query_params.get('session_id') #getting url params 
        if not query_param_session:
            raise ValueError('Stripe checkout session id is missing.')

        #getting the customer's stripe session
        customer_session = stripe.checkout.Session.retrieve(
                api_key=request.app.state.stripe_api_key,
                id=query_param_session
        )
        if customer_session.customer != cache_data['customer_stripe_id']:
            raise ValueError('Stripe checkout session does not match this customer.')
        #getting the payment id from session
        setup_intent_id = customer_session.setup_intent
        if not setup_intent_id:
            raise ValueError('Stripe setup was not completed.')
        setup_intent = stripe.SetupIntent.retrieve(
            api_key=request.app.state.stripe_api_key,
            id=setup_intent_id
        )
        stripe_payment_id = setup_intent.payment_method
        if not stripe_payment_id:
            raise ValueError('Stripe did not return a saved payment method.')
        if setup_intent.status != 'succeeded':
            raise ValueError('Stripe card setup has not succeeded.')
        payment_method = stripe.PaymentMethod.retrieve(
            api_key=request.app.state.stripe_api_key,
            id=stripe_payment_id
        )
        if payment_method.customer != cache_data['customer_stripe_id']:
            raise ValueError('Saved payment method does not belong to this Stripe customer.')

        existing_method_query = await session_db.execute(select(StripePayment).where(and_(
            StripePayment.customer_id == customer.id,
            StripePayment.stripe_payment_id == stripe_payment_id
        )))
        if existing_method_query.scalar_one_or_none():
            await cache_db.delete(cache_key)
            return StripePaymentResponse(response='Payment method was already saved.')

        #creating the new Payment model for the customer 
        new_payment = StripePayment(
            name=customer.name,
            stripe_customer_id=cache_data.get('customer_stripe_id'),
            stripe_payment_id=stripe_payment_id,
            customer_id=customer.id,
            created_at=datetime.now(timezone.utc)
        )

        #staging/commiting new payment 
        session_db.add(new_payment)
        await session_db.commit()
            
        #deleting old cache key 
        await cache_db.delete(cache_key)

        #returning the response -> client 
        return StripePaymentResponse(
            response='Payment method was successfully added.'
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail='Invalid card setup session.') from error
    except Exception as error:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail='Unable to save the payment method. Please try again.'
        ) from error
    
#failed route
@customer_home_router.get('/payment/add/failed', response_model=StripePaymentResponse)
async def payment_creation_failed(cache_db:Annotated[CacheDatabase, Depends(get_cache_db)],
                                  customer_id:str):
    #clearing the cache 
    try:
        cache_key = f'{str(UUID(customer_id))}/stripe'
    except ValueError as error:
        raise HTTPException(status_code=400, detail='Invalid card setup session.') from error
    try:
        await cache_db.delete(
            key=cache_key
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Unable to clear pending card setup. Please try again.'
        )

    #returning response to client 
    return StripePaymentResponse(
        response='Unable to add payment. Please try again.'
    )
