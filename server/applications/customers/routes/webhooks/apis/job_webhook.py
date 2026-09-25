#File for the webhook for the agent jobs completed
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.app import get_relational_db_session
from server.models.auths.api_auth import MerchantAPI
from server.models.activities.jobs.agent_job import (
    AgentJob,
    AgentJobState
)
from server.applications.customers.schemas.webhooks.webhook_schema import (
    AgentCompletedJob
)
from server.applications.customers.services.webhooks.webhook_service import get_merchants_api_key
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated
from uuid import UUID

customer_api_webhook_router = APIRouter('/customer/webhooks', tags=['Router for the apis webhooks'])

"""Route for the webhook for the completed job"""
@customer_api_webhook_router.post('/requests')
async def update_customer_job(merchant_api_model:Annotated[MerchantAPI, Depends(get_merchants_api_key)],
                              agent_completed_job:AgentCompletedJob,
                              session_db:Annotated[AsyncSession, Depends(get_relational_db_session)]):
    pass