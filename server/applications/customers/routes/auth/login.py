#File for the routes for the customer login
from fastapi.exceptions import HTTPException
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from server.applications.customers.routes.auth.signup import customer_auth_router
from server.dependencies import (
    get_relational_db_session,
    get_cache_db,
    get_servers_number,
    get_twilio_client,
    get_server_key,
)
from server.models.users.customers import Customer
from server.models.auths.authentications import SessionAuthentication
from server.models.auths.verifications import (
    SMSVerification,
    VerificationState
)
from server.applications.customers.schemas.auth.login import (
    CustomerLogin,
    CustomerLoginResponse,
    CustomerLogoutResponse,
)
from server.applications.customers.services.auth.auth_service import (
    generate_code,
    send_message,
    AuthState,
    bearer_scheme,
    get_current_customer,
)
from server.config.database import CacheDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from twilio.rest import Client
from pydantic_extra_types.phone_numbers import PhoneNumber
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID, uuid4
import hashlib
import hmac
import json

"""Route for the customer to login"""
@customer_auth_router.post('/login', response_model=CustomerLoginResponse)
async def customer_login(customer_info:CustomerLogin,
                         session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                         cache_db:Annotated[CacheDatabase, Depends(get_cache_db)],
                         twilio_client:Annotated[Client, Depends(get_twilio_client)],
                         pine_number:Annotated[PhoneNumber, Depends(get_servers_number)]):
    #database query for the customer
    try:
        customer_query = await session_db.execute(select(Customer).where(and_(
            Customer.email == customer_info.email,
            Customer.phonenumber == customer_info.phonenumber
        )))
        customer = customer_query.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Database error. Please try logining in again.'
        )

    #check for if customer exists 
    if not customer:
        raise HTTPException(
            status_code=400,
            detail='An account does not exist at this email and phonenumber.'
        )

    #storing the customers name
    customer_data_str = json.dumps({
        'name':customer.name
    })

    customer_code = generate_code() #generating verification code
    #creating the customer's verification row 
    customer_verification = SMSVerification(
        name=customer.name,
        phonenumber=customer.phonenumber,
        verification_attempts=0,
        verification_state=VerificationState.PENDING,
        auth_state=AuthState.LOGIN,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    customer_verification.code = customer_code #hashing the code 

    #adding new verification to postgres
    try:
        session_db.add(customer_verification)
        await session_db.flush()
        await session_db.commit()
    except Exception:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail='Database error. Please try logining in again.'
        )

    customer_exp_token = str(uuid4())
    #caching the customer's data
    try:
        await cache_db.insert(str(customer_verification.id), customer_data_str)
        await cache_db.insert(customer_exp_token, str(customer_verification.id))
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Database error. Please try logining in again.'
        )

    #sending message over to the customer
    message_body = f'Pine verification code: {customer_code}'
    try:
        send_message(twilio_client, 
                     customer.phonenumber, 
                     pine_number, 
                     message_body
                )
    except RuntimeError:
        raise HTTPException(
            status_code=400,
            detail='Unable to send verification code via sms. Try logining in again.'
        )

    #returning info from the client
    return CustomerLoginResponse(
        token=customer_exp_token,
        response='Pine verification has been sent to you. Via sms.'
    )


"""Route to revoke the customer's current authenticated session."""
@customer_auth_router.post('/logout', response_model=CustomerLogoutResponse)
async def customer_logout(
    customer_credentials:Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    customer:Annotated[Customer, Depends(get_current_customer)],
    session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
    PINE_SERVER_KEY:Annotated[str, Depends(get_server_key)],
):
    # Match only this customer's session token, which is stored as an HMAC hash.
    try:
        token_uuid = UUID(customer_credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail='Invalid customer session token.')

    token_hash = hmac.new(
        PINE_SERVER_KEY.encode('utf-8'),
        token_uuid.bytes,
        hashlib.sha256
    ).hexdigest().encode('utf-8')

    try:
        session_query = await session_db.execute(select(SessionAuthentication).where(and_(
            SessionAuthentication.customer_id == customer.id,
            SessionAuthentication.session_token == token_hash
        )))
        customer_session = session_query.scalar_one_or_none()

        if not customer_session:
            raise HTTPException(status_code=404, detail='Customer session was not found.')

        # Delete this device's session so the same token cannot authenticate again.
        await session_db.delete(customer_session)
        await session_db.commit()
    except HTTPException:
        raise
    except Exception as error:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail='Unable to end this customer session.'
        ) from error

    return CustomerLogoutResponse(response='You have been logged out.')
