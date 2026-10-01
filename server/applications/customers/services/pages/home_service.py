#File for the helper fucntions in the home page routes
from server.applications.customers.schemas.pages.home_schemas import (
    ReturnedPayments
)
from server.models.integrations.stripe_payments.stripe_payment import StripePayment
from server.models.activities.jobs.agent_job import (
    AgentJob,
    AgentJobState
)
from server.models.users.customers import Customer
from server.models.agents.hired_agent import HiredAgent
from server.models.agents.agent import Agent, AgentState
from server.applications.customers.schemas.webhooks.webhook_schema import CachedClientJob
from server.models.activities.transactions.job_payments import JobPayments
from server.models.notifications.notification_message import (
    Notification,
    NotificationState,
    NotificationType,
)
from server.applications.customers.schemas.pages.home_schemas import IndividualNotification
from server.applications.customers.agent.customer_agent import MessageType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from server.config.database import CacheDatabase
from server.config.apis import NotificationEvents
from aiohttp import ClientSession
from stripe import StripeClient
import json
import hashlib
import hmac
from datetime import datetime, timezone
from uuid import UUID
import asyncio


def get_pending_job_queue_key(customer_id: UUID | str, hired_agent_id: UUID | str) -> str:
    """Build the Redis list key for one customer's hired-agent queue."""
    return f'{customer_id}/{hired_agent_id}'

#Helper function -> loops through payments lst creates -> stores pydantic model
async def get_returned_payments_lst(payments_lst:list[StripePayment], stripe_client:StripeClient):
    returned_lst = [] #lst to return the pydantic payments

    #looping through lst
    for payment in payments_lst:
        returned_payment = ReturnedPayments(
            payment_id=str(payment.id)
        )

        #using stripe api to get customer data info
        try:
            # Retrieve the exact method represented by this saved Pine record.
            stripe_payment_method = await asyncio.to_thread(
                stripe_client.v1.payment_methods.retrieve,
                payment.stripe_payment_id,
            )
            if stripe_payment_method.customer != payment.stripe_customer_id:
                raise ValueError('Saved payment method does not belong to its Stripe customer.')
            if not stripe_payment_method.card:
                raise ValueError('Saved payment method is not a card.')
            card_data = stripe_payment_method.card
            returned_payment.payment_last4 = card_data.last4
            returned_payment.payment_card_type = card_data.brand
            returned_payment.expires_at = f"{card_data.exp_month:02d}/{card_data.exp_year}"

            returned_lst.append(returned_payment) #appending the payment to lst 
        except Exception as err:
            raise err

    return returned_lst #returning the lst of pydantic payments 

#helper function to pay for the job
def create_job_payment_intent(
    stripe_client:StripeClient,
    cached_job:CachedClientJob,
    customer_payment:StripePayment,
    idempotency_key:str,
):
    """Create or retrieve the same PaymentIntent for this exact cached offer."""
    return stripe_client.v1.payment_intents.create(
        {
            'amount':cached_job.job_price,
            'currency':'usd',
            'customer':customer_payment.stripe_customer_id,
            'metadata':{
                'customer_id':str(cached_job.customer_id),
                'hired_agent_id':str(cached_job.agent_id),
                'offer_id':str(cached_job.offer_id),
                'agent_name':cached_job.agent_name,
                'job_name':cached_job.job_name,
                'job_description':cached_job.job_description,
                'job_price':str(cached_job.job_price),
            },
        },
        {'idempotency_key':idempotency_key},
    )


async def create_or_retrieve_paid_job(
    session_db:AsyncSession,
    customer:Customer,
    cached_job:CachedClientJob,
    hired_agent:HiredAgent,
    payment_intent_id:str,
):
    """Create the job and its payment row in one durable database transaction."""
    if hired_agent.customer_id != customer.id or hired_agent.id != cached_job.agent_id:
        raise ValueError('The hired agent for this job could not be found.')

    existing_payment_query = await session_db.execute(select(JobPayments).where(
        JobPayments.offer_id == cached_job.offer_id
    ))
    existing_payment = existing_payment_query.scalar_one_or_none()

    if existing_payment:
        if existing_payment.stripe_payment_intent_id != payment_intent_id:
            raise ValueError('This offer is already linked to another payment.')
        existing_job_query = await session_db.execute(select(AgentJob).where(
            AgentJob.id == existing_payment.agent_job_id
        ))
        existing_job = existing_job_query.scalar_one_or_none()
        if not existing_job:
            raise ValueError('The paid job record could not be found.')
        return existing_job, existing_payment, False

    agent_job = AgentJob(
        job_name=cached_job.job_name,
        job_description=cached_job.job_description,
        job_price=cached_job.job_price,
        job_state=AgentJobState.ACTIVE,
        hired_agent_id=hired_agent.id,
        customer_id=customer.id,
        hired_agent_name=hired_agent.name,
        assigned_at=datetime.now(timezone.utc),
    )
    payment_record = JobPayments(
        job_name=cached_job.job_name,
        job_description=cached_job.job_description,
        job_price=cached_job.job_price,
        agent_job_id=agent_job.id,
        hired_agent_id=hired_agent.id,
        customer_id=customer.id,
        hired_agent_name=hired_agent.name,
        offer_id=cached_job.offer_id,
        stripe_payment_intent_id=payment_intent_id,
        created_at=datetime.now(timezone.utc),
        paid_at=datetime.now(timezone.utc),
    )

    try:
        session_db.add(agent_job)
        await session_db.flush()
        session_db.add(payment_record)
        await session_db.commit()
        return agent_job, payment_record, True
    except IntegrityError:
        await session_db.rollback()
        #A webhook and the customer request may finalize the same offer together.
        existing_payment_query = await session_db.execute(select(JobPayments).where(
            JobPayments.offer_id == cached_job.offer_id
        ))
        existing_payment = existing_payment_query.scalar_one_or_none()
        if not existing_payment or existing_payment.stripe_payment_intent_id != payment_intent_id:
            raise
        existing_job_query = await session_db.execute(select(AgentJob).where(
            AgentJob.id == existing_payment.agent_job_id
        ))
        existing_job = existing_job_query.scalar_one_or_none()
        if not existing_job:
            raise ValueError('The paid job record could not be found.')
        return existing_job, existing_payment, False
    except Exception:
        await session_db.rollback()
        raise


def _cached_job_from_payment_intent(payment_intent) -> CachedClientJob:
    """Rebuild an offer from server-written Stripe metadata after Redis expiry."""
    metadata = payment_intent.metadata
    return CachedClientJob(
        customer_id=UUID(metadata['customer_id']),
        agent_id=UUID(metadata['hired_agent_id']),
        agent_name=metadata['agent_name'],
        job_name=metadata['job_name'],
        job_description=metadata['job_description'],
        job_price=int(metadata['job_price']),
        offer_id=UUID(metadata['offer_id']),
    )


async def finalize_paid_job(
    session_db:AsyncSession,
    cache_db:CacheDatabase,
    http_client:ClientSession,
    pine_server_key:str,
    notification_events:NotificationEvents,
    payment_intent,
    customer:Customer | None = None,
):
    """Persist and dispatch a successful job payment idempotently by offer ID."""
    if payment_intent.status != 'succeeded':
        raise ValueError('The job payment has not succeeded.')

    try:
        cached_job = _cached_job_from_payment_intent(payment_intent)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError('Payment metadata does not contain a valid job offer.') from error

    if customer is None:
        customer_query = await session_db.execute(select(Customer).where(
            Customer.id == cached_job.customer_id
        ))
        customer = customer_query.scalar_one_or_none()
    if not customer or customer.id != cached_job.customer_id:
        raise ValueError('The customer for this payment was not found.')

    if payment_intent.amount != cached_job.job_price or payment_intent.currency != 'usd':
        raise ValueError('The payment amount does not match the job offer.')

    saved_method_query = await session_db.execute(select(StripePayment.id).where(and_(
        StripePayment.customer_id == customer.id,
        StripePayment.stripe_customer_id == payment_intent.customer,
        StripePayment.stripe_payment_id == payment_intent.payment_method,
    )))
    if not saved_method_query.scalar_one_or_none():
        raise ValueError('This payment method is not connected to the customer.')

    hired_agent_query = await session_db.execute(select(HiredAgent).where(and_(
        HiredAgent.id == cached_job.agent_id,
        HiredAgent.customer_id == customer.id,
    )))
    hired_agent = hired_agent_query.scalar_one_or_none()
    if not hired_agent:
        raise ValueError('The hired agent for this payment was not found.')

    existing_payment_query = await session_db.execute(select(JobPayments).where(
        JobPayments.offer_id == cached_job.offer_id
    ))
    existing_payment = existing_payment_query.scalar_one_or_none()
    if not existing_payment and hired_agent.agent_state != AgentState.ACTIVE:
        raise ValueError('The hired agent is no longer active.')

    agent_job, payment_record, created = await create_or_retrieve_paid_job(
        session_db=session_db,
        customer=customer,
        cached_job=cached_job,
        hired_agent=hired_agent,
        payment_intent_id=payment_intent.id,
    )

    #Remove the exact offer only after its paid job is safely stored in Postgres.
    queue_key = get_pending_job_queue_key(customer.id, hired_agent.id)
    queued_jobs = await cache_db.retrieve_lst(queue_key)
    for queued_job_value in queued_jobs:
        try:
            queued_job = CachedClientJob.model_validate_json(queued_job_value)
        except Exception:
            continue
        if queued_job.offer_id == cached_job.offer_id:
            await cache_db.remove_list_item(queue_key, queued_job_value)
            break

    if payment_record.dispatched_at is None:
        agent_query = await session_db.execute(select(Agent).where(
            Agent.id == hired_agent.agent_id
        ))
        agent = agent_query.scalar_one_or_none()
        if not agent:
            raise ValueError('Unable to locate the hired agent endpoint.')

        agent_job_model = {
            'customer_id':str(customer.id),
            'job_id':str(agent_job.id),
            'job_name':agent_job.job_name,
            'job_description':agent_job.job_description,
            'agent_restrictions':hired_agent.agent_restrictions,
        }
        serialized_job = json.dumps(agent_job_model, separators=(',', ':'))
        signature = hmac.new(
            pine_server_key.encode('utf-8'),
            serialized_job.encode('utf-8'),
            digestmod=hashlib.sha256,
        ).hexdigest()

        async with http_client.post(
            url=agent.agents_webhook_url,
            headers={
                'Content-Type':'application/json',
                'Signature':signature,
                'Idempotency-Key':str(agent_job.id),
            },
            data=serialized_job,
        ) as response:
            if response.status < 200 or response.status >= 300:
                raise RuntimeError('The agent endpoint did not accept the paid job.')

        #Persist notifications and the dispatch marker together so retries do not duplicate rows.
        customer_notification = Notification(
            notification_header=f'Your agent {agent_job.hired_agent_name} has just been sent a job',
            notification_message=f'Agent {agent_job.hired_agent_name} has just been sent the job {agent_job.job_name}.',
            notification_type=NotificationType.JOB_ACTION,
            notification_state=NotificationState.UNREAD,
            customer_id=customer.id,
            created_at=datetime.now(timezone.utc),
        )
        merchant_notification = Notification(
            notification_header='New Payment Incoming.',
            notification_message=f'Your agent {agent.name} has just been given a job.',
            notification_type=NotificationType.JOB_ACTION,
            notification_state=NotificationState.UNREAD,
            merchant_id=agent.merchant_id,
            created_at=datetime.now(timezone.utc),
        )
        payment_record.dispatched_at = datetime.now(timezone.utc)
        session_db.add_all([customer_notification, merchant_notification])
        try:
            await session_db.commit()
        except Exception:
            await session_db.rollback()
            raise

        try:
            await notification_events.event_set(data={
                'customer_id':str(customer.id),
                'customer_noti':{
                    'noti_id':str(customer_notification.id),
                    'noti_header':customer_notification.notification_header,
                    'noti_message':customer_notification.notification_message,
                    'noti_type':customer_notification.notification_type,
                },
            })
        except Exception:
            #Notifications are already durable in Postgres and can be fetched by the client.
            pass

    return agent_job, payment_record, created

#creating the agents new job 
async def create_agents_new_job(session_db:AsyncSession, 
                                customer:Customer,
                                cached_job:CachedClientJob,
                                hired_agent:HiredAgent):
    if hired_agent.customer_id != customer.id or hired_agent.id != cached_job.agent_id:
        raise ValueError('The hired agent for this job could not be found.')

    #building sql model for the new job
    agent_new_job = AgentJob(
        job_name=cached_job.job_name,
        job_description=cached_job.job_description,
        job_price=cached_job.job_price,
        job_state=AgentJobState.ACTIVE,
        hired_agent_id=hired_agent.id,
        customer_id=hired_agent.customer_id,
        hired_agent_name=hired_agent.name,
        assigned_at=datetime.now(timezone.utc)
    )

    #staging and commiting the new agent job
    try:
        session_db.add(agent_new_job)
        await session_db.commit()
    except Exception as err:
        await session_db.rollback() #rolling back on the staged commit
        raise err

    return agent_new_job #returning sql model for agent job

#getting the hired agent's url 
async def get_hired_agent_url(session_db:AsyncSession, hired_agent:HiredAgent):
    try:
        agent_query = await session_db.execute(select(Agent).where(
            Agent.id == hired_agent.agent_id
        ))
        agent = agent_query.scalar_one_or_none()
    except Exception as err:
        raise err

    #check if agent queried
    if not agent:
        raise Exception('Unable to locate agent from query')

    return agent #returning the agent 

#helper function to create new job payment 
async def create_new_job_payment(session_db:AsyncSession, agent_job:AgentJob):
    try:
        new_job_payment = JobPayments(
            job_name=agent_job.job_name,
            job_description=agent_job.job_description,
            job_price=agent_job.job_price,
            agent_job_id=agent_job.id,
            hired_agent_id=agent_job.hired_agent_id,
            customer_id=agent_job.customer_id,
            hired_agent_name=agent_job.hired_agent_name,
            created_at=datetime.now(timezone.utc),
            paid_at=datetime.now(timezone.utc)
        )

        #staging/committing the newly added payment 
        session_db.add(new_job_payment)
        await session_db.commit()
    except Exception as error:
        await session_db.rollback()
        raise error
    return new_job_payment

#Helper fucntion -> reads from customer notis list -> stores in strawberry avaliable field 
def get_notification_returned(customer_notifications:list[Notification]):
    returned_lst = [] #lst returning the notifications 

    #looping through the notifications
    for notification in customer_notifications:
        returned_notification = IndividualNotification(
            noti_id=str(notification.id),
            noti_header=notification.notification_header,
            noti_message=notification.notification_message,
            noti_type=notification.notification_type,
            notification_date=notification.created_at.strftime("%b %d, %Y")
        )

        returned_lst.append(returned_notification) #appending the notification to lst

    return returned_lst #returning lst

"""Helper functions to get the agents message"""
#returns the router agent message
def create_router_agent_message(previous_context:list[str],
                                customer_message:str):
    return json.dumps({
        'context':previous_context,
        'content':customer_message
    })

#returns the tooling agent message 
def create_tooling_agent_message_str(previous_context:list[str], 
                        hired_agent_id:str,
                        customer_id:str,
                        customer_message:str):
    #message dict
    message_content = {
        'hired_agent_id':hired_agent_id,
        'customer_id':customer_id,
        'content':customer_message
    }

    #returning the payload message
    return json.dumps(
        {
            'message': {
                'context':previous_context,
                'content':message_content
            }
        }
    )

#returned context for the tooling agent
def return_tooling_agent_context(customer_message:str, agent_response:str):
    return {
        'content': {
        'message':customer_message,
        'response':agent_response
        }
    }

#returned context for the router agent 
def return_router_agent_context(customer_message:str, message_type:MessageType):
    return {
        'content': {
            'message_type':message_type.value,
            'message':customer_message
        }
    }
