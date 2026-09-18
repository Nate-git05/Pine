#File for the signup route for the customer 
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.app import (
    get_relational_db_session, 
    get_cache_db,
    get_twilio_client,
    get_servers_number
)
from server.models.users.customers import Customer
from server.models.auths.verifications import (
    SMSVerification,
    VerificationState
)
from server.applications.customers.schemas.auth.signup import (
    CustomerSignup,
    CustomerSignupResponse
)
from server.config.database import CacheDatabase
from server.applications.customers.services.auth.auth_service import (
    generate_code,
    send_message,
    AuthState
)
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing import Annotated
from twilio.rest import Client
from datetime import datetime, timezone
from redis.asyncio import RedisError
from uuid import uuid4
import json

customer_auth_router = APIRouter(prefix='/auth/customer', tags=['Auth routes for the customer'])

"""Route for the customer to signup for the application"""
@customer_auth_router.post('/signup', response_model=CustomerSignupResponse)
async def customer_signup(customer_info:CustomerSignup, 
                          session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                          cache_db:Annotated[CacheDatabase, Depends(get_cache_db)],
                          twilio_client:Annotated[Client, Depends(get_twilio_client)],
                          pine_number:Annotated[PhoneNumber, Depends(get_servers_number)]):
    #database query to see if account exists under the same phonenumber
    try:
        customer_query = await session_db.execute(select(Customer).where(and_(
            Customer.email == customer_info.email,
            Customer.phonenumber == customer_info.phonenumber
        )))
        customer = customer_query.scalar_one_or_none() #gets the first customer row found
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Database error. Please try signing up again later.'
        )

    #checking if customer already exists 
    if customer:
        raise HTTPException(
            status_code=400,
            detail='An account under this email and phonenumber already exists.'
        )

    #storing customer info in json -> wait till verification to create model
    customer_json_str = json.dumps({
            'name':f'{customer_info.first_name} {customer_info.last_name}',
            'email':str(customer_info.email),
            'phonenumber':str(customer_info.phonenumber)
        })

    user_code = generate_code() #generating users code for verification

    #creating the customers verification row
    customer_verification = SMSVerification(
        name=f'{customer_info.first_name} {customer_info.last_name}',
        phonenumber=customer_info.phonenumber,
        verification_attempts=0,
        verification_state=VerificationState.PENDING,
        auth_state=AuthState.SIGNUP,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    customer_verification.code = user_code 

    #adding the verification to Postgres
    try:
        session_db.add(customer_verification)
        await session_db.flush() #retreiving the created ID
        await session_db.commit()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Database error. Please try signing up again later.'
        )

    #sending sms message over to the customer
    message_body = f'Pine verification code: {user_code}'
    try:
        send_message(twilio_client, customer_info.phonenumber, 
                     pine_number, message_body)
    except RuntimeError:
        raise HTTPException(
            status_code=400,
            detail='Unable to send over verification code. Please try signing up later.'
        )

    #caching the id and customer info 
    customer_exp_token = uuid4()
    try:
        await cache_db.insert(str(customer_exp_token), str(customer_verification.id))
        await cache_db.insert(str(customer_verification.id), customer_json_str)
    except RedisError:
        raise HTTPException(
            status_code=500,
            detail='Database error. Please try signing up again later.'
        )
    #returning exp token to client 
    return CustomerSignupResponse(
        customer_token=str(customer_exp_token)
    )