"""Public landing-page registration endpoint for merchant leads."""
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.dependencies import get_relational_db_session
from server.landing.merchants.schemas.register import (
    MerchantRegistration,
    MerchantRegistrationResponse,
)
from server.models.registrations.merchant_registration import MerchantRegistrationModel


merchant_landing_router = APIRouter(
    prefix='/landing/register',
    tags=['Registration routes router.'],
)


@merchant_landing_router.post('/merchant', response_model=MerchantRegistrationResponse)
async def merchant_registration(
    registration_info: MerchantRegistration,
    session_db: Annotated[AsyncSession, Depends(get_relational_db_session)],
) -> MerchantRegistrationResponse:
    # Keep merchant registrations in their own table, separate from customer leads.
    try:
        existing_registration_query = await session_db.execute(
            select(MerchantRegistrationModel).where(or_(
                MerchantRegistrationModel.email == registration_info.email,
                MerchantRegistrationModel.phonenumber == registration_info.phonenumber,
            ))
        )
        existing_registration = existing_registration_query.scalar_one_or_none()
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail='Database issue. Please try registering later.',
        ) from error

    if existing_registration:
        raise HTTPException(
            status_code=400,
            detail='A merchant registration already exists for this email or phone number.',
        )

    new_registration = MerchantRegistrationModel(
        first_name=registration_info.first_name,
        last_name=registration_info.last_name,
        email=str(registration_info.email),
        phonenumber=str(registration_info.phonenumber),
        registered_at=datetime.now(UTC),
    )

    try:
        session_db.add(new_registration)
        await session_db.commit()
    except Exception as error:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail='Unable to save the merchant registration. Please try again later.',
        ) from error

    return MerchantRegistrationResponse(
        response=f'Thanks for registering, {registration_info.first_name}. We will be in touch.',
    )
