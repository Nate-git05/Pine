#File for the verification route for the customer's sms code 
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.applications.customers.routes.auth.signup import customer_auth_router
from server.app import (
    get_relational_db_session,
    get_servers_number,
    get_twilio_client,
    get_cache_db,
    get_server_key
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
from server.models.auths.authentications import SessionAuthentication
from server.applications.customers.services.auth.auth_service import (
    generate_code,
    send_message,
    AuthState
)
from server.config.database import CacheDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from twilio.rest import Client
from typing import Annotated
from pydantic_extra_types.phone_numbers import PhoneNumber
from redis.asyncio import RedisError
from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4
import json
import hashlib
import hmac

"""Route for the customer to verify sms code"""
@customer_auth_router.post('/verify/{customer_token}', response_model=CustomerSignupResponse)
async def customer_verify(customer_info:CustomerSMSVerify, customer_token:str,
                          session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                          cache_db:Annotated[CacheDatabase, Depends(get_cache_db)],
                          twilio_client:Annotated[Client, Depends(get_twilio_client)],
                          pine_number:Annotated[PhoneNumber, Depends(get_servers_number)],
                          PINE_SEVER_SECRET_KEY:Annotated[str, Depends(get_server_key)]):
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
            status_code=405,
            detail='Database error. Please try signing in again.'
        )

    #checking if the customer entered right code 
    if not customer_verification.check_code(customer_info.code):
        customer_verification.verification_attempts += 1 #incrementing verification attempts

        #checking if customer entered wrong code 3 times -> if so replace code send em new one
        if customer_verification.verification_attempts >= 3:
            new_customer_code = generate_code()
            customer_verification.code = new_customer_code #setting new code hash in the verification
            customer_verification.verification_attempts = 0
            customer_verification.updated_at = datetime.now(timezone.utc)
            try:     
                await session_db.commit()
            except Exception:
                await session_db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail='Database error. Please try rentering the verification code.'
                )

            #recaching the customer data and the verification id
            try:
                await cache_db.insert(str(customer_verification.id), json.dumps(customer_data_dict))
                await cache_db.insert(customer_token, str(customer_verification.id))
            except RedisError:
                raise HTTPException(
                    status_code=500,
                    detail='Database error. Please try rentering the verification code.'
                )

            message_body = f'Pine verification code: {new_customer_code}'
            try:
                send_message(
                    twilio_client, 
                    customer_verification.phonenumber, 
                    pine_number, 
                    message_body
                )
            except RuntimeError:
                raise HTTPException(
                    status_code=400,
                    detail='Having trouble resending Pine verification code. Please try again.'
                )

            #returning the customer token back to the client 
            return CustomerSignupResponse(
                customer_token=customer_token,
                response='Max attempts reached. New verification code has been sent via sms.'
            )

        #updating the changes made to the row
        customer_verification.updated_at = datetime.now(timezone.utc)
        try:
            await session_db.commit()
        except Exception:
            await session_db.rollback()
            raise HTTPException(
                status_code=500,
                detail='Database error. Please try rentering the verification code.'
            )

    #updating the verification attributes
    customer_verification.verification_state = VerificationState.ACCEPTED
    customer_verification.verified_at = datetime.now(timezone.utc)
    customer_verification.updated_at = datetime.now(timezone.utc)

    #checking the auth state 
    if customer_verification.auth_state == AuthState.SIGNUP:
        #creating new customer 
        new_customer = Customer(
            name=customer_data_dict.get('name'),
            email=customer_data_dict.get('email'),
            phonenumber=customer_data_dict.get('phonenumber'),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    #mapping created model -> postgres table
    try:
        session_db.add(new_customer)
        await session_db.flush()
        await session_db.commit()
    except Exception:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail='Database error. Please try again rentering the code.'
        )

    customer_session_token = uuid4() #generating customer session token
    #hashing the customers token
    token_hash = hmac.new(
        PINE_SEVER_SECRET_KEY.encode('utf-8'),
        customer_session_token.bytes,
        hashlib.sha256
    ).hexdigest().encode('utf-8')

    #creating the customer's authentication row
    customer_authentication = SessionAuthentication(
        name=new_customer.name,
        customer_id=new_customer.id,
        session_token=token_hash,
        token_exp_time=datetime.now(timezone.utc) + timedelta(days=60),
        created_at=datetime.now(timezone.utc)
    )

    #mapping new row to Postgres 
    try:
        session_db.add(customer_authentication)
        await session_db.commit()
    except Exception:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail='Database error. Please try again rentering the code.'
        )

    #returning customer's session token 
    return CustomerSignupResponse(
        customer_token=str(customer_token),
        response=f'{new_customer.name}, congratulations! Your signup is successful.'
    )

"""Route for the customer to request a new code"""
@customer_auth_router.patch('/verify/update/{customer_token}', response_model=CustomerSignupResponse)
async def update_customer_code(customer_token:str, 
                               session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                               cache_db:Annotated[CacheDatabase, Depends(get_cache_db)],
                               twilio_client:Annotated[Client, Depends(get_twilio_client)],
                               pine_number:Annotated[PhoneNumber, Depends(get_servers_number)]):
    #retrieving the values from cache 
    try:
        customer_verification_id:str = await cache_db.retrieve(customer_token)
        if not customer_verification_id:
            raise HTTPException(
                status_code=404,
                detail='Verification session has expired or is invalid.'
            )

        customer_data_str = await cache_db.retrieve(customer_verification_id)
        if not customer_data_str:
            raise HTTPException(
                status_code=404,
                detail='Signup session data not found.'
            )
    except RedisError:
        raise HTTPException(
            status_code=500,
            detail='Temporary cache service interruption. Please try again.'
        )

    #casting the verification id str -> UUID
    try:
        verification_id = UUID(customer_verification_id)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail='Malformed verification identifier format.'
        )

    #database query for the customer verification
    try:
        customer_verification_query = await session_db.execute(select(SMSVerification).where(
            SMSVerification.id == verification_id
        ))
        customer_verification = customer_verification_query.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Database connection failure while retrieving records.'
        )

    #check if verification was queryed 
    if not customer_verification:
        raise HTTPException(
            status_code=400,
            detail='No verification record matches this request'
        )

    new_customer_code = generate_code() #generating new customer code 
    #updating row attributes
    customer_verification.code = new_customer_code
    customer_verification.verification_attempts = 0
    customer_verification.updated_at = datetime.now(timezone.utc)

    try:
        await session_db.commit()
    except Exception:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail='Failed to persist the new verification code'
        )

    #recaching the data in redis 
    try:
        await cache_db.insert(customer_token, str(verification_id))
        await cache_db.insert(str(verification_id), customer_data_str)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Failed to renew cache state.'
        )

    #sending new verification code over to customer
    message_body = f'Pine verification code: {new_customer_code}'
    try:
        send_message(twilio_client,
                     customer_verification.phonenumber,
                     pine_number,
                     message_body
                     )
    except RuntimeError:
        raise HTTPException(
            status_code=400,
            detail='Failed to send sms message for new veriifcation code. Please try again.'
        )

    #returning info to the client 
    return CustomerSignupResponse(
        customer_token=customer_token,
        response='Verification code resent successfully.'
    )