#File for the Rest method to get the customers profile page
import asyncio
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.applications.customers.services.auth.auth_service import get_current_customer
from server.dependencies import (
    get_relational_db_session,
    get_stripe_api_key
)
from server.models.users.customers import Customer
from server.models.integrations.stripe_payments.stripe_payment import StripePayment
from server.models.agents.hired_agent import (
    HiredAgent,
    AgentState
)
from server.models.activities.jobs.agent_job import (
    AgentJob,
    AgentJobState
)
from server.applications.customers.schemas.pages.profile_schemas import (
    CustomerProfile
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from typing import Annotated
import stripe

#global router for the customer's profile page
customer_profile_router = APIRouter(prefix='/profile', tags=['Router for customer\'s profile page'])

"""Route to get customer\'s profile page info"""
@customer_profile_router.get('/page')
async def get_customer_profile(customer:Annotated[Customer, Depends(get_current_customer)],
                               session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                               stripe_api_key:Annotated[str, Depends(get_stripe_api_key)]):
    #database query for the customer
    try:
        #customer payments
        customer_latest_payment_query = await session_db.execute(select(StripePayment).where(
            StripePayment.customer_id == customer.id
        ).order_by(desc(StripePayment.last_used)).limit(1))
        customer_latest_payment = customer_latest_payment_query.scalar_one_or_none()

        #customer agents
        customer_hired_agents_query = await session_db.execute(select(HiredAgent).where(and_(
             HiredAgent.customer_id == customer.id,
             HiredAgent.agent_state == AgentState.ACTIVE
        )))
        customer_hired_agents = customer_hired_agents_query.scalars().all()

        #database query for customer jobs
        customer_jobs_query = await session_db.execute(select(AgentJob).where(and_(
            AgentJob.customer_id == customer.id,
            AgentJob.job_state == AgentJobState.DONE
        )))
        customer_jobs = customer_jobs_query.scalars().all()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Unable to load the customer profile. Please try again.'
        )

    #check if customer has a payment -> id so get payment details
    if customer_latest_payment:
        try:
            stripe_payment_method = await asyncio.to_thread(
                stripe.PaymentMethod.retrieve,
                api_key=stripe_api_key,
                id=customer_latest_payment.stripe_payment_id
            )
        except Exception:
            raise HTTPException(
                status_code=400,
                detail='Unable to retrieve the saved payment method.'
            )

    #pydantic model -> returned to client
    returned_customer = CustomerProfile(
        customer_name=customer.name,
        customer_email=customer.email,
        customer_number=customer.phonenumber,
        card_type=stripe_payment_method.card.brand if customer_latest_payment else None,
        active_card_last4=stripe_payment_method.card.last4 if customer_latest_payment else None,
        expire_date=(
            f'{stripe_payment_method.card.exp_month:02d}/{str(stripe_payment_method.card.exp_year)[-2:]}'
            if customer_latest_payment else None
        ),
        number_of_agents=len(customer_hired_agents) if customer_hired_agents else 0,
        jobs_completed=len(customer_jobs) if customer_jobs else 0
    )

    return returned_customer #returning customer info to client for profile
