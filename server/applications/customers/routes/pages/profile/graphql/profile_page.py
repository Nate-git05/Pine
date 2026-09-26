#File for the profile page for the customer
import strawberry
from strawberry import (
    Info,
    Schema
)
from strawberry.fastapi import GraphQLRouter
from server.applications.customers.services.auth.auth_service import get_customer_context
from server.models.users.customers import Customer
from server.applications.customers.schemas.pages.activities_schema import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

"""Client side query for the customer\'s profile page"""
@strawberry.type
class ProfilePage:
    @strawberry.field
    async def get_customer_profile(self, customer_info:Info):
        #getting the context of of customer
        try:
            session_db:AsyncSession = customer_info.context.get('database_session')
            customer:Customer = customer_info.context.get('customer')
        except Exception:
            return HTTPException(
                status_code=400,
                detail='Unable to get the profile page please try again.'
            )