#File for the helper/dependency functions for auth and routes
import string 
import secrets
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.requests import Request
from server.dependencies import (
    get_relational_db_session,
    get_server_key
)
from server.models.users.customers import Customer
from server.models.auths.authentications import SessionAuthentication
from server.applications.customers.schemas.auth.customer_context import CustomerContextRequest
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
bearer_scheme = HTTPBearer() #strips the token from request

#authorizes customers session with the server
async def get_current_customer(
    customer_credentials:Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
    PINE_SERVER_KEY:Annotated[str, Depends(get_server_key)]
):
    customer_token = customer_credentials.credentials

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
    customer_credentials:Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
    PINE_SERVER_KEY:Annotated[str, Depends(get_server_key)]
) -> dict:
    customer_token = customer_credentials.credentials

    #reading request data for cursor pagination
    try:
        request_data = CustomerContextRequest.model_validate_json(
            await request.body()
        )
    except Exception:
        try:
            request_data = CustomerContextRequest.model_validate(
                dict(request.query_params)
            )
        except Exception:
            request_data = CustomerContextRequest()

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
    if not customer_session:
        raise HTTPException(
            status_code=404,
            detail='Unable to locate customer\'s session.'
        )

    #check if session expired
    now = datetime.now(timezone.utc)
    session_valid = now < customer_session.token_exp_time
    if not session_valid:
        customer_session.expired_at = now
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
    if not customer:
        raise HTTPException(
            status_code=400,
            detail='Unable to locate customer. Please try signing back in.'
        )

    try:
        customer_session.validated_at = now #validating the customer session token
        await session_db.commit() #committing change made
    except Exception:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail='Database error. Session handling went wrong.'
        )

    #getting the GraphQL variables
    variables = request_data.variables

    #checking if the client is requesting the next page
    cursor = request_data.cursor
    if cursor is None and variables:
        cursor = variables.cursor

    #getting the last datetime id seen by the client
    last_id_seen = request_data.last_id_seen or request_data.last_date or request_data.last_seen
    if not last_id_seen and variables:
        last_id_seen = variables.last_id_seen or variables.last_date or variables.last_seen

    if isinstance(last_id_seen, datetime) and last_id_seen.tzinfo is None:
        last_id_seen = last_id_seen.replace(tzinfo=timezone.utc)

    #returning the customer and cursor data to the GraphQL routes
    return {
        'customer': customer,
        'database_session': session_db,
        'cursor': cursor,
        'last_id_seen': last_id_seen,
        'last_seen': last_id_seen,
    }

#dependency function to retrive the validated customer
async def get_customer(context_info:Annotated[dict, Depends(get_customer_context)]):
    return {
        'customer':context_info.get('customer'),
        'database_session':context_info.get('database_session'),
        'cursor':context_info.get('cursor'),
        'last_id_seen':context_info.get('last_id_seen'),
        'last_seen':context_info.get('last_seen')
    }
