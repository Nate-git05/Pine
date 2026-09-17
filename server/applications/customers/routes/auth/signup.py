#File for the signup route for the customer 
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.app import get_relational_db_session
from server.models.users.customers import Customer
from server.applications.customers.schemas.auth.signup import CustomerSignup
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
import json

customer_auth_router = APIRouter(prefix='/customer/auth', tags=['Auth routes for the customer'])

"""Route for the customer to signup for the application"""
@customer_auth_router.post('/signup')
async def customer_signup(customer_info:CustomerSignup, 
                          session_db:Annotated[AsyncSession, Depends(get_relational_db_session)]):
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
            detail=''
        )

    #checking if customer already exists 
    if customer:
        raise HTTPException(
            status_code=400,
            detail=''
        )

    #storing customer info in json -> wait till verification to create model
    customer_json_str = json.dumps({
            'name':f'{customer_info.first_name} {customer_info.last_name}',
            'email':str(customer_info.email),
            'phonenumber':str(customer_info.phonenumber)
        })

    user_code = _ #generating users code for verification
     