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
from server.models.activities.transactions.job_payments import JobPayments
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import stripe
from datetime import datetime, timezone

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
            #getting customer payment method
            stripe_payment_method = stripe.PaymentMethod.list(
                api_key=stripe_api_key,
                customer=payment.stripe_customer_id,
                type='card'
            )

            #check if any data in the payment method
            if not stripe_payment_method.data:
                raise Exception('Unable to get the payment data for the customer from stripe')

            #looping though the stripe methods 
            for card_data in stripe_payment_method.data:
                #updating pydantic model
                returned_payment.payment_last4 = card_data.card.last4
                returned_payment.payment_card_type = card_data.card.brand
                returned_payment.expires_at = f"{card_data.card.exp_month:02d}/{card_data.card.exp_year}"

            returned_lst.append(returned_payment) #appending the payment to lst 
        except Exception as err:
            raise err

    return returned_lst #returning the lst of pydantic payments 

#helper function to pay for the job
def customer_payment_for_job(cached_job:dict, customer_payment:StripePayment, stripe_api_key:str):
    #starting the stripe payment
    try:
        payment_intet = stripe.PaymentIntent.create(
            api_key=stripe_api_key,
            amount=cached_job.get('job_price'),
            currency='usd',
            customer=customer_payment.stripe_customer_id,
            payment_method=customer_payment.stripe_payment_id,
            confirm=True,
            off_session=True
        )
    except Exception as error:
        raise error

    return payment_intet

#creating the agents new job 
async def create_agents_new_job(session_db:AsyncSession, 
                                customer:Customer,
                                cached_job:dict):
    try:
        hired_agent_query = await session_db.execute(select(HiredAgent).where(and_(
            HiredAgent.id == cached_job.get('agent_id'),
            HiredAgent.customer_id == customer.id
        )))
        hired_agent = hired_agent_query.scalar_one_or_none() #getting the agent from customer id and the agents id
    except Exception as err:
        raise err

    if not hired_agent:
        raise ValueError('The hired agent for this job could not be found.')

    #building sql model for the new job
    agent_new_job = AgentJob(
        job_name=cached_job.get('job_name'),
        job_description=cached_job.get('job_description'),
        job_price=cached_job.get('job_price'),
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
