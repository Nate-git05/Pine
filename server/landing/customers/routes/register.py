#File for the customer registration route 
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.app import get_relational_db_session
from server.landing.customers.schemas.register import (
    CustomerRegistration,
    CustomerRegistrationResponse
)
from server.models.registrations.customer_registration import CustomerRegisterModel
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from datetime import datetime, UTC

landing_router = APIRouter(prefix='/landing/register', tags=['Registration routes router.'])

"""Route for the customer to register"""
@landing_router.post('/customer', response_model=CustomerRegistrationResponse)
async def customer_registration(registration_info:CustomerRegistration, 
                                session_db:Annotated[AsyncSession, Depends(get_relational_db_session)]):
    #database query for existing registration
    try:
        registration_query = await session_db.execute(select(CustomerRegisterModel).where(or_(
            CustomerRegisterModel.email == registration_info.email,
            CustomerRegisterModel.phonenumber == registration_info.phonenumber
        )))
        customer_registration = registration_query.scalar_one_or_none() #returns first found row 
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Database issues. Please try registering later.'
        )

    #check if user already registered
    if customer_registration:
        raise HTTPException(
            status_code=400,
            detail='That email or phone number is already registered.'
        )

    #registering the new customer 
    new_registration = CustomerRegisterModel(
        first_name=registration_info.first_name,
        last_name=registration_info.last_name,
        email=registration_info.email,
        phonenumber=registration_info.phonenumber,
        registered_at=datetime.now(UTC)
    )

    #adding new customer registration to Postgres
    try:
        session_db.add(new_registration)
        await session_db.commit() #committing change to the database
    except Exception:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail='Unable to update database. Please try registering later.'
        )

    return CustomerRegistrationResponse(
        response=f'Success! Thanks for registering, {registration_info.first_name}.'
    )