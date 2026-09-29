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
from server.models.agents.agent import Agent
from server.applications.customers.schemas.webhooks.webhook_schema import CachedClientJob
from server.models.activities.transactions.job_payments import JobPayments
from server.models.notifications.notification_message import Notification
from server.applications.customers.schemas.pages.home_schemas import IndividualNotification
from server.applications.customers.agent.customer_agent import MessageType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import stripe
from datetime import datetime, timezone
from uuid import UUID


def get_pending_job_queue_key(customer_id: UUID | str, hired_agent_id: UUID | str) -> str:
    """Build the Redis list key for one customer's hired-agent queue."""
    return f'{customer_id}/{hired_agent_id}'

#Helper function -> loops through payments lst creates -> stores pydantic model
def get_returned_payments_lst(payments_lst:list[StripePayment], stripe_api_key:str):
    returned_lst = [] #lst to return the pydantic payments

    #looping through lst
    for payment in payments_lst:
        returned_payment = ReturnedPayments(
            payment_id=str(payment.id)
        )

        #using stripe api to get customer data info
        try:
            # Retrieve the exact method represented by this saved Pine record.
            stripe_payment_method = stripe.PaymentMethod.retrieve(
                api_key=stripe_api_key,
                id=payment.stripe_payment_id
            )
            if stripe_payment_method.customer != payment.stripe_customer_id:
                raise ValueError('Saved payment method does not belong to its Stripe customer.')
            card_data = stripe_payment_method.card
            returned_payment.payment_last4 = card_data.last4
            returned_payment.payment_card_type = card_data.brand
            returned_payment.expires_at = f"{card_data.exp_month:02d}/{card_data.exp_year}"

            returned_lst.append(returned_payment) #appending the payment to lst 
        except Exception as err:
            raise err

    return returned_lst #returning the lst of pydantic payments 

#helper function to pay for the job
def customer_payment_for_job(cached_job:CachedClientJob, customer_payment:StripePayment, stripe_api_key:str,
                             idempotency_key:str | None = None):
    #starting the stripe payment
    try:
        payment_intet = stripe.PaymentIntent.create(
            api_key=stripe_api_key,
            amount=cached_job.job_price,
            currency='usd',
            customer=customer_payment.stripe_customer_id,
            payment_method=customer_payment.stripe_payment_id,
            confirm=True,
            off_session=True,
            idempotency_key=idempotency_key
        )
    except Exception as error:
        raise error

    return payment_intet

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
                        customer_message:str):
    #message dict
    message_content = {
        'hired_agent_id':hired_agent_id,
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
