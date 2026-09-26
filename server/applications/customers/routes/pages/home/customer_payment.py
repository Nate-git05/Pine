#File for the routes for the customers payments 
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.applications.customers.routes.pages.home.agent_chat import customer_home_router
from server.app import (
    get_relational_db_session,
    get_stripe_client,
    get_cache_db
)
from server.applications.customers.services.auth.auth_service import get_current_customer
from server.models.users.customers import Customer
from server.models.integrations.stripe_payments.stripe_payment import (
    StripePayment,
    PaymentState
)
from server.config.database import CacheDatabase
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from stripe import StripeClient
from typing import Annotated

"""Route for the customer to pay for the job"""
@customer_home_router.post('/payment')
async def customer_job_payment(customer:Annotated[Customer, Depends(get_current_customer)],
                               stripe_client:Annotated[StripeClient, Depends(get_stripe_client)],
                               session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                               cache_db:Annotated[CacheDatabase, Depends(get_cache_db)]):
    #database query for the payment 
    try:
        stripe_payment_query = await session_db.execute(select(StripePayment).where(and_(
            StripePayment.customer_id == customer.id,
            StripePayment.payment_state == PaymentState.ACTIVE
        )))
        customer_payment = stripe_payment_query.scalar_one_or_none()
    except Exception:
        raise HTTPException()

    #if query returns none -> open Stripe payment 
    if not customer_payment:
        pass

    #getting redis list from cache
    try:
        pass
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=''
        )
    