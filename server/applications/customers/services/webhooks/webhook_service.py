#Service file for the helper functions in webhook routes
from fastapi.requests import Request
from fastapi.exceptions import HTTPException
from server.models.auths.api_auth import MerchantAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

"""Dependency function to retrieve the merchants api key"""
async def get_merchants_api_key(request:Request):
    #getting the database session 
    try:
        database_session:AsyncSession = request.app.state.relational_database 
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Unable to retrieve application info.'
        )

    #getting the api key from the request
    try:
        merchant_api_key_str = request.headers.get('Api-Key')
        merchant_api_key = UUID(merchant_api_key_str) #casting api key str -> uuid 

        #database query for the merchant
        merchant_api_query = await database_session.execute(select(MerchantAPI).where(
            MerchantAPI.api_key == merchant_api_key
        ))
        merchant_api_model = merchant_api_query.scalar_one_or_none() #gets the first api model found

        #check if model was queired 
        if not merchant_api_model:
            raise HTTPException(
                status_code=400,
                detail='Unable to validate api key.'
            )

        #returning the merchant api model to route
        return merchant_api_model
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Database error. Request failed.'
        )