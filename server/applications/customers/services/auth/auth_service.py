#File for the helper/dependency functions for auth and routes
import string 
import secrets
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.requests import Request
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
import json

"""Helper functions for the auth routes"""
#function to generate user six digit code
def generate_code(limit:int=6):
    code = ''.join(secrets.choice(string.digits) for _ in range(limit))

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
    except Exception as error:
        raise RuntimeError('Unable to send the verification message.') from error

"""Enum to define the state of the auth"""
class AuthState(StrEnum):
    SIGNUP='signup'
    LOGIN='login'

"""Dependency function for session auths"""
#Rest methods 
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
            status_code=404,
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
            detail='Database error. Session handling went wrong.'
        )

    #check if session exists 
    if (not customer_session):
        raise HTTPException(
            status_code=404,
            detail='Unable to locate customer\'s session.'
        )

    #check if session expired 
    session_valid = datetime.now(timezone.utc) < customer_session.token_exp_time
    if not session_valid:
        customer_session.expired_at = datetime.now(timezone.utc)
        try:
            await session_db.commit()
        except Exception:
            await session_db.rollback()
            raise HTTPException(
                status_code=500,
                detail='Database error. Session handling went wrong.'
            )

        raise HTTPException(
            status_code=404,
            detail='Session expired. Please login again.'
        )

    try:
        customer_session.validated_at = datetime.now(timezone.utc) #validating the customer session token
        await session_db.commit() #committing change made 
    except Exception:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail='Database error. Session handling went wrong.'
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
            detail='Database error. Session handling went wrong.'
        )

    #check if customer was queried
    if not customer:
        raise HTTPException(
            status_code=400,
            detail='Unable to locate customer. Please try signing back in.'
        )

    return customer #returning customer to server route 

#GraphQL routes 
#context getter to validate database session with customer
async def get_customer_context(
    request:Request,
    session_db:Annotated[AsyncSession, Depends(get_relational_db_session)]
) -> dict:
    """Authenticate GraphQL requests using the same token scheme as REST."""
    try:
        request_data = await request.json()
    except Exception as error:
        raise HTTPException(status_code=400, detail='The request body is missing or invalid.') from error

    authorization = request.headers.get('Authorization', '')
    scheme, _, token_value = authorization.partition(' ')
    if scheme.lower() != 'bearer' or not token_value.strip():
        raise HTTPException(status_code=401, detail='Please sign in to continue.')
    try:
        customer_token = UUID(token_value.strip())
    except ValueError as error:
        raise HTTPException(status_code=401, detail='Invalid session token.') from error

    secret = request.app.state.server_key
    customer_token_hash = hmac.new(
        secret.encode('utf-8'), customer_token.bytes, hashlib.sha256
    ).hexdigest().encode('utf-8')
    session_query = await session_db.execute(select(SessionAuthentication).where(
        SessionAuthentication.session_token == customer_token_hash
    ))
    customer_session = session_query.scalar_one_or_none()
    if not customer_session:
        raise HTTPException(status_code=401, detail='Invalid session token.')
    now = datetime.now(timezone.utc)
    if now >= customer_session.token_exp_time:
        customer_session.expired_at = now
        await session_db.commit()
        raise HTTPException(status_code=401, detail='Session expired. Please sign in again.')

    customer_query = await session_db.execute(select(Customer).where(
        Customer.id == customer_session.customer_id
    ))
    customer = customer_query.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=401, detail='Customer account was not found.')
    customer_session.validated_at = now
    await session_db.commit()

    variables = request_data.get('variables') or {}
    last_date = variables.get('last_date', request_data.get('last_date'))
    if isinstance(last_date, str):
        try:
            last_date = datetime.fromisoformat(last_date.replace('Z', '+00:00'))
        except ValueError:
            last_date = None
    return {
        'customer': customer,
        'database_session': session_db,
        'cursor': variables.get('cursor', request_data.get('cursor')),
        'last_date': last_date,
        'last_made': last_date,
        'last_active_job': last_date,
        'last_id_seen': last_date,
    }

#dependency function to retrive the validated customer
async def get_customer(context_info:Annotated[dict, Depends(get_customer_context)]):
    return {
        'customer':context_info.get('customer'),
        'database_session':context_info.get('database_session'),
        'cursor':context_info.get('cursor'),
        'last_date':context_info.get('last_date')
    }
