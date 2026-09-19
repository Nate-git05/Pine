#File for the helper/dependency functions for auth and routes
import string 
import random
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer
from server.app import (
    get_relational_db_session,
    get_server_key
)
from server.models.users.customers import Customer
from server.models.auths.authentications import SessionAuthentication
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic_extra_types.phone_numbers import PhoneNumber
from twilio.rest import Client
from sqlalchemy import select
from enum import StrEnum
from typing import Annotated
from datetime import datetime, timezone
from uuid import UUID
import hmac 
import hashlib

"""Helper functions for the auth routes"""
#function to generate user six digit code
def generate_code(limit:int=6):
    code = ''.join(random.choices(string.digits, k=limit))

    return code #returns random six digit num

#function to send sms with twilio api
def send_message(twilio_client:Client, user_number:PhoneNumber, 
                 pine_number:PhoneNumber, body:str):
    try:
        _ = twilio_client.messages.create(
            to=user_number,
            from_=pine_number,
            body=body
        )
    except RuntimeError as error:
        raise error

"""Enum to define the state of the auth"""
class AuthState(StrEnum):
    SIGNUP='signup'
    LOGIN='login'

"""Dependency function for session auths"""
oauth2_scheme = OAuth2PasswordBearer() #strips the token from request

#authorizes customers session with the server
async def get_current_customer(customer_token:Annotated[str, Depends(oauth2_scheme)],
                               session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                               PINE_SERVER_KEY:Annotated[str, Depends(get_server_key)]):
    #casting the token to UUID
    try:
        token_uuid = UUID(customer_token)
    except Exception:
        raise HTTPException(
            status_code=405,
            detail='Database error. Invalid token shape.'
        )

    #hashing the token 
    token_hash = hmac.new(
        PINE_SERVER_KEY.encode('utf-8'),
        token_uuid.bytes,
        hashlib.sha256
    ).hexdigest().encode('utf-8')

    #database query for the token
    try:
        session_query = await session_db.execute(select(SessionAuthentication).where(
            SessionAuthentication.session_token == token_hash
        ))
        customer_session = session_query.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=''
        )

    #check if session exists 
    session_valid = datetime.now(timezone.utc) > customer_session.token_exp_time
    if (not customer_session) or session_valid:
        customer_session.expired_at = datetime.now(timezone.utc)
        try:
            await session_db.commit()
        except Exception:
            await session_db.rollback()
            raise HTTPException(
                status_code=500,
                detail=''
            )
        
        raise HTTPException(
            status_code=405,
            detail=''
        )
    
    customer_session.validated_at = datetime.now(timezone.utc) #validating the customer session token
    try:
        await session_db.commit() #committing change made 
    except Exception:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail=''
        )

    #database query for the customer
    try:
        customer_query = await session_db.execute(select(Customer).where(
            Customer.id == customer_session.customer_id
        ))
        customer = customer_query.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=''
        )

    #check if customer was queried
    if not customer:
        raise HTTPException(
            status_code=500,
            detail=''
        )

    return customer #returning customer to server route
    

