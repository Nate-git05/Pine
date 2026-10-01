#File for the routes for the customers payments 
from fastapi.requests import Request
from fastapi.exceptions import HTTPException
from fastapi import Depends
import asyncio
from server.applications.customers.routes.pages.home.agent_chat import customer_home_router
from server.dependencies import (
    get_relational_db_session,
    get_stripe_client,
    get_cache_db,
    get_async_http,
    get_server_key,
    get_notifications_events
)
from server.applications.customers.services.auth.auth_service import get_current_customer
from server.models.users.customers import Customer
from server.models.activities.jobs.agent_job import AgentJob, AgentJobState
from server.models.agents.hired_agent import HiredAgent
from server.models.agents.agent import AgentState
from server.models.integrations.stripe_payments.stripe_payment import StripePayment
from server.models.activities.transactions.job_payments import JobPayments
from server.applications.customers.schemas.pages.home_schemas import (
    ReturnedPaymentsList,
    PaymentResponse,
    StripePaymentResponse
)
from server.applications.customers.services.pages.home_service import (
    get_returned_payments_lst,
    create_job_payment_intent,
    finalize_paid_job,
    get_pending_job_queue_key,
)
from server.applications.customers.schemas.webhooks.webhook_schema import CachedClientJob
from server.config.database import CacheDatabase
from server.config.apis import NotificationEvents
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, NAMESPACE_URL, uuid5
from typing import Annotated
from aiohttp import ClientSession
from datetime import datetime, timezone
from stripe import StripeClient, StripeError
import json

"""Route for the customer to pay for the job"""
@customer_home_router.get('/cards', response_model=ReturnedPaymentsList)
async def get_customer_cards(customer:Annotated[Customer, Depends(get_current_customer)],
                             stripe_client:Annotated[StripeClient, Depends(get_stripe_client)],
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
        payments_lst = await get_returned_payments_lst(customer_payments, stripe_client)
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
@customer_home_router.post('/payment/{payment_id_str}/{agent_id_str}/{offer_id_str}', response_model=PaymentResponse)
async def customer_job_payment(payment_id_str:str,
                               agent_id_str:str,
                               offer_id_str:str,
                               customer:Annotated[Customer, Depends(get_current_customer)], 
                               session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                               cache_db:Annotated[CacheDatabase, Depends(get_cache_db)],
                               stripe_client:Annotated[StripeClient, Depends(get_stripe_client)],
                               http_client:Annotated[ClientSession, Depends(get_async_http)],
                               pine_server_key:Annotated[str, Depends(get_server_key)],
                               notification_events:Annotated[NotificationEvents, Depends(get_notifications_events)]):
    #casting payment id str -> uuid
    try:
        payment_id = UUID(payment_id_str)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail='Invalid payment id. Please select a saved card and try again.'
        )

    try:
        agent_id = UUID(agent_id_str)
    except ValueError as error:
        raise HTTPException(status_code=400, detail='Invalid agent id. Please select the offer again.') from error

    try:
        offer_id = UUID(offer_id_str)
    except ValueError as error:
        raise HTTPException(status_code=400, detail='Invalid job offer. Please select the offer again.') from error

    #Resume an already-paid offer before checking current queue or agent state.
    try:
        existing_payment_query = await session_db.execute(select(JobPayments).where(and_(
            JobPayments.customer_id == customer.id,
            JobPayments.hired_agent_id == agent_id,
            JobPayments.offer_id == offer_id,
        )))
        existing_job_payment = existing_payment_query.scalar_one_or_none()
    except Exception as error:
        raise HTTPException(status_code=500, detail='Unable to check the payment status.') from error

    if existing_job_payment and existing_job_payment.stripe_payment_intent_id:
        try:
            payment_intent = await asyncio.to_thread(
                stripe_client.v1.payment_intents.retrieve,
                existing_job_payment.stripe_payment_intent_id,
            )
            await finalize_paid_job(
                session_db=session_db,
                cache_db=cache_db,
                http_client=http_client,
                pine_server_key=pine_server_key,
                notification_events=notification_events,
                payment_intent=payment_intent,
                customer=customer,
            )
            return PaymentResponse(
                response='This offer was already paid and its job status has been refreshed.',
                status='succeeded',
                payment_intent_id=payment_intent.id,
            )
        except Exception:
            return PaymentResponse(
                response='Payment succeeded. Pine is retrying job delivery; check activity before trying again.',
                status='processing',
                payment_intent_id=existing_job_payment.stripe_payment_intent_id,
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
            detail='Unable to look up the saved payment method. Please try again.'
        )

    #check if query returned None
    if not customer_payment:
        raise HTTPException(
            status_code=400,
            detail='That saved payment method was not found for your account.'
        )

    # Read this hired-agent's list and find the exact offer without consuming it.
    queue_key = get_pending_job_queue_key(customer.id, agent_id)
    try:
        queued_jobs = await cache_db.retrieve_lst(queue_key)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Unable to retrieve the pending job. Please submit the job again.'
        )

    cached_job_value = None
    try:
        for queued_job_value in queued_jobs:
            queued_job = CachedClientJob.model_validate_json(queued_job_value)
            if queued_job.offer_id == offer_id:
                cached_job_value = queued_job_value
                break
    except Exception as error:
        raise HTTPException(status_code=500, detail='A cached job offer is invalid.') from error

    if not cached_job_value:
        raise HTTPException(
            status_code=400,
            detail='Unable to process the payment. Check your payment method and try again.'
        )

    try:
        cached_job = CachedClientJob.model_validate_json(cached_job_value)
    except Exception as error:
        raise HTTPException(status_code=400, detail='The cached job offer is invalid.') from error

    if cached_job.offer_id != offer_id or cached_job.customer_id != customer.id:
        raise HTTPException(status_code=400, detail='This job offer does not belong to this customer.')

    if cached_job.agent_id != agent_id:
        raise HTTPException(status_code=400, detail='This job offer does not belong to the selected agent.')

    if not queued_jobs or queued_jobs[0] != cached_job_value:
        raise HTTPException(status_code=409, detail='This offer is queued behind another job.')

    # Verify the active hire and current job state before charging the customer.
    try:
        hired_agent_query = await session_db.execute(select(HiredAgent).where(and_(
            HiredAgent.id == cached_job.agent_id,
            HiredAgent.customer_id == customer.id,
            HiredAgent.agent_state == AgentState.ACTIVE,
        )))
        hired_agent = hired_agent_query.scalar_one_or_none()
        if not hired_agent:
            raise ValueError('This offer is not from an active hired agent.')

        active_job_query = await session_db.execute(select(AgentJob.id).where(and_(
            AgentJob.hired_agent_id == hired_agent.id,
            AgentJob.customer_id == customer.id,
            AgentJob.job_state == AgentJobState.ACTIVE,
        )).limit(1))
        if active_job_query.scalar_one_or_none():
            raise ValueError('This agent is already working on a job.')
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail='Unable to validate this job offer.') from error

    #Create one durable Stripe payment attempt for the offer, then confirm it while the customer is present.
    try:
        idempotency_key = str(uuid5(
                NAMESPACE_URL,
                f'pine:job-offer:{customer.id}:{offer_id}',
            ))
        payment_intent = await asyncio.to_thread(
            create_job_payment_intent,
            stripe_client,
            cached_job,
            customer_payment,
            idempotency_key,
        )

        #A prior request may have created the intent before its response was lost.
        if payment_intent.status == 'requires_payment_method':
            payment_intent = await asyncio.to_thread(
                stripe_client.v1.payment_intents.confirm,
                payment_intent.id,
                {
                    'payment_method':customer_payment.stripe_payment_id,
                    'off_session':False,
                },
            )
    except StripeError as error:
        raise HTTPException(
            status_code=402,
            detail='Stripe could not complete this payment. Select a different saved card or try again.',
        ) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail='Unable to start the job payment.') from error

    if payment_intent.status == 'requires_action':
        if payment_intent.payment_method != customer_payment.stripe_payment_id:
            raise HTTPException(
                status_code=409,
                detail='This offer is awaiting authentication with its original card. Finish that step before changing cards.',
            )
        return PaymentResponse(
            response='Your bank requires an authentication step to complete this payment.',
            status='requires_action',
            payment_intent_id=payment_intent.id,
            client_secret=payment_intent.client_secret,
        )

    if payment_intent.status == 'processing':
        return PaymentResponse(
            response='Payment is processing. Pine will send the job when Stripe confirms it.',
            status='processing',
            payment_intent_id=payment_intent.id,
        )

    if payment_intent.status != 'succeeded':
        raise HTTPException(
            status_code=402,
            detail=f'Payment did not succeed (status: {payment_intent.status}). Select a saved card and retry.',
        )

    try:
        agent_job, _, _ = await finalize_paid_job(
            session_db=session_db,
            cache_db=cache_db,
            http_client=http_client,
            pine_server_key=pine_server_key,
            notification_events=notification_events,
            payment_intent=payment_intent,
            customer=customer,
        )
    except Exception:
        return PaymentResponse(
            response='Payment succeeded. Pine is retrying job delivery; check activity before trying again.',
            status='processing',
            payment_intent_id=payment_intent.id,
        )

    #returning success to the client
    return PaymentResponse(
        response=f'Payment succeeded. Agent is beginning job {agent_job.id}.',
        status='succeeded',
        payment_intent_id=payment_intent.id,
    )


@customer_home_router.post('/payment/confirm/{payment_intent_id}', response_model=PaymentResponse)
async def confirm_customer_job_payment(
    payment_intent_id:str,
    customer:Annotated[Customer, Depends(get_current_customer)],
    session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
    cache_db:Annotated[CacheDatabase, Depends(get_cache_db)],
    stripe_client:Annotated[StripeClient, Depends(get_stripe_client)],
    http_client:Annotated[ClientSession, Depends(get_async_http)],
    pine_server_key:Annotated[str, Depends(get_server_key)],
    notification_events:Annotated[NotificationEvents, Depends(get_notifications_events)],
):
    """Finalize a job after the mobile app completes any required Stripe authentication."""
    try:
        payment_intent = await asyncio.to_thread(
            stripe_client.v1.payment_intents.retrieve,
            payment_intent_id,
        )
    except StripeError as error:
        raise HTTPException(status_code=404, detail='Unable to find this payment.') from error

    if payment_intent.metadata.get('customer_id') != str(customer.id):
        raise HTTPException(status_code=404, detail='Unable to find this payment.')

    if payment_intent.status == 'requires_action':
        return PaymentResponse(
            response='Complete the authentication request from your bank to continue.',
            status='requires_action',
            payment_intent_id=payment_intent.id,
            client_secret=payment_intent.client_secret,
        )

    if payment_intent.status == 'processing':
        return PaymentResponse(
            response='Payment is processing. Pine will send the job when Stripe confirms it.',
            status='processing',
            payment_intent_id=payment_intent.id,
        )

    if payment_intent.status != 'succeeded':
        raise HTTPException(status_code=402, detail='The job payment has not succeeded. Select a card and try again.')

    try:
        agent_job, _, _ = await finalize_paid_job(
            session_db=session_db,
            cache_db=cache_db,
            http_client=http_client,
            pine_server_key=pine_server_key,
            notification_events=notification_events,
            payment_intent=payment_intent,
            customer=customer,
        )
    except Exception:
        return PaymentResponse(
            response='Payment succeeded. Pine is retrying job delivery; check activity before trying again.',
            status='processing',
            payment_intent_id=payment_intent.id,
        )

    return PaymentResponse(
        response=f'Payment succeeded. Agent is beginning job {agent_job.id}.',
        status='succeeded',
        payment_intent_id=payment_intent.id,
    )

"""Route for the customer to add a card"""
@customer_home_router.post('/payment/add')
async def add_customer_payment(customer:Annotated[Customer, Depends(get_current_customer)],
                               cache_db:Annotated[CacheDatabase, Depends(get_cache_db)],
                               stripe_client:Annotated[StripeClient, Depends(get_stripe_client)],
                               session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                               request:Request):
    #Reuse the customer ID independently of whether a saved card currently exists.
    customer_stripe_id = customer.stripe_customer_id
    if not customer_stripe_id:
        try:
            customer_stripe = await asyncio.to_thread(
                stripe_client.v1.customers.create,
                {
                    'email':str(customer.email),
                    'name':customer.name,
                    'metadata':{'pine_customer_id':str(customer.id)},
                },
                {'idempotency_key':f'pine-customer-{customer.id}'},
            )
            customer_stripe_id = customer_stripe.id
            customer.stripe_customer_id = customer_stripe_id
            await session_db.commit()
        except Exception as error:
            raise HTTPException(
                status_code=500,
                detail='Unable to prepare Stripe customer details for card setup.',
            ) from error

    #caching the customer's payment 
    cache_key = f'{str(customer.id)}/stripe'
    try:
        data = json.dumps({
            'customer_stripe_id':customer_stripe_id,
        })
        await cache_db.insert(cache_key, data, exp_time=600)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Unable to save card setup details. Please try again.'
        )

    #creating customers stripe session -> stripe to create payment id
    try:
        stripe_session = await asyncio.to_thread(
            stripe_client.v1.checkout.sessions.create,
            {
                'mode':'setup',
                'customer':customer_stripe_id,
                'success_url':(
                    f'{request.url_for("created_payment_model")}'
                    f'?session_id={{CHECKOUT_SESSION_ID}}&customer_id={customer.id}'
                ),
                'cancel_url':(
                    f'{request.url_for("payment_creation_failed")}'
                    f'?customer_id={customer.id}'
                ),
                'metadata':{'pine_customer_id':str(customer.id)},
                'setup_intent_data':{
                    'usage':'off_session',
                    'metadata':{'pine_customer_id':str(customer.id)},
                },
            },
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
                                cache_db:Annotated[CacheDatabase, Depends(get_cache_db)],
                                stripe_client:Annotated[StripeClient, Depends(get_stripe_client)]):
    try:
        customer_id = UUID(request.query_params.get('customer_id', ''))
        cache_key = f'{str(customer_id)}/stripe'

        cached_setup = await cache_db.retrieve(key=cache_key)
        if not cached_setup:
            raise ValueError('Pending Stripe customer data is missing.')
        
        cache_data:dict = json.loads(cached_setup)
        if not cache_data or not cache_data.get('customer_stripe_id'):
            raise ValueError('Pending Stripe customer data is missing.')

        customer_query = await session_db.execute(select(Customer).where(
            Customer.id == customer_id
        ))
        customer = customer_query.scalar_one_or_none()

        if not customer:
            raise ValueError('Customer account was not found.')

        #getting customer's stripe session
        query_param_session = request.query_params.get('session_id') #getting url params 
        if not query_param_session:
            raise ValueError('Stripe checkout session id is missing.')

        #getting the customer's stripe session
        customer_session = await asyncio.to_thread(
            stripe_client.v1.checkout.sessions.retrieve,
            query_param_session,
        )

        if customer_session.mode != 'setup' or customer_session.status != 'complete':
            raise ValueError('Stripe checkout session is not a completed card setup.')
        if customer_session.customer != cache_data['customer_stripe_id']:
            raise ValueError('Stripe checkout session does not match this customer.')
        #getting the payment id from session
        setup_intent_id = customer_session.setup_intent

        if not setup_intent_id:
            raise ValueError('Stripe setup was not completed.')
        setup_intent = await asyncio.to_thread(
            stripe_client.v1.setup_intents.retrieve,
            setup_intent_id,
        )

        #getting the stripe -> check if the method was succesfully returned 
        stripe_payment_id = setup_intent.payment_method
        if not stripe_payment_id:
            raise ValueError('Stripe did not return a saved payment method.')
        if setup_intent.status != 'succeeded':
            raise ValueError('Stripe card setup has not succeeded.')

        #retrieving the payment from the payment id 
        payment_method = await asyncio.to_thread(
            stripe_client.v1.payment_methods.retrieve,
            stripe_payment_id,
        )

        #checking if cached stripe customer id == to stripe stored customer id 
        if payment_method.customer != cache_data['customer_stripe_id']:
            raise ValueError('Saved payment method does not belong to this Stripe customer.')

        #check for if payment already exists
        existing_method_query = await session_db.execute(select(StripePayment).where(and_(
            StripePayment.customer_id == customer.id,
            StripePayment.stripe_payment_id == stripe_payment_id
        )))
        if existing_method_query.scalar_one_or_none():
            await cache_db.delete(cache_key)
            return StripePaymentResponse(response='Payment method was already saved.')

        if customer.stripe_customer_id and customer.stripe_customer_id != cache_data['customer_stripe_id']:
            raise ValueError('Stripe customer does not match this customer account.')
        customer.stripe_customer_id = cache_data['customer_stripe_id']

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
async def payment_creation_failed(customer_id:str):
    #The short-lived setup cache expires automatically. Do not let an unauthenticated redirect
    #delete another customer's pending setup data by supplying their customer ID.
    try:
        UUID(customer_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail='Invalid card setup session.') from error
    #returning response to client 
    return StripePaymentResponse(
        response='Unable to add payment. Please try again.'
    )
