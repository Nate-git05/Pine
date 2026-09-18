#File for the verification route for the customer's sms code 
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.applications.customers.routes.auth.signup import customer_auth_router
from server.app import (
    get_relational_db_session,
    get_servers_number,
    get_twilio_client,
    get_cache_db
)
from server.applications.customers.schemas.auth.signup import (
    CustomerSMSVerify,
    CustomerSignupResponse
)
from server.models.users.customers import Customer
from server.models.auths.verifications import (
    SMSVerification,
    VerificationState
)
from server.config.database import CacheDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from twilio.rest import Client
from typing import Annotated
from pydantic_extra_types.phone_numbers import PhoneNumber
from redis.asyncio import RedisError
from datetime import datetime, UTC
from uuid import UUID
import json

"""Route for the customer to verify sms code"""
@customer_auth_router.post('/verify/{token}')
async def customer_verify(customer_info:CustomerSMSVerify, customer_token:str,
                          session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                          cache_db:Annotated[CacheDatabase, Depends(get_cache_db)],
                          twilio_client:Annotated[Client, Depends(get_twilio_client)],
                          pine_number:Annotated[PhoneNumber, Depends(get_servers_number)]):
    #retrieving values in cache 
    try:
        customer_verification_id:str = await cache_db.retrieve(customer_token)
        if not customer_verification_id:
            raise HTTPException(
                status_code=402,
                detail='Signup expired. Please try signing up again.'
            )
        
        customer_info_str:str = await cache_db.retrieve(customer_verification_id)
        if not customer_info_str:
            raise HTTPException(
                status_code=405,
                detail='Signup expired. Please try signing up again.'
            )
        
        customer_data_dict:dict = json.loads(customer_info_str) #loading in the customer str as dict
    except RedisError:
        raise HTTPException(
            status_code=500,
            detail="Database error. Please try rentering the code again."
        )

    #casting verification id str -> UUID
    try:
        verification_id = UUID(customer_verification_id)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=''
        )

    #query for the customers verification 
    try:
        customer_verification_query = await session_db.execute(select(SMSVerification).where(
            SMSVerification.id == verification_id
        ))
        customer_verification = customer_verification_query.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Database error. Please try again rentering the code.'
        )

    #check if customer verification retrieved
    if not customer_verification:
        raise HTTPException(
            status_code=400,
            detail=''
        )

    #checking if the customer entered right code 
    if not customer_verification.check_code(customer_info.code):
        pass

    #updating the verification attributes
    customer_verification.verification_state = VerificationState.ACCEPTED
    customer_verification.verified_at = datetime.now(UTC)

    #customer enters correct code -> create auth and customer row
    new_customer = Customer(
        name=customer_data_dict.get('name'),
        email=customer_data_dict.get('email'),
        phonenumber=customer_data_dict.get('phonenumber'),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )

    #mapping created model -> postgres table
    try:
        session_db.add(new_customer)
        await session_db.flush()
        await session_db.commit()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=''
        )

    #creating customer's auth table
    pass