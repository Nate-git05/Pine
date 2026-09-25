#File for the webhook for the agent jobs completed
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.app import get_relational_db_session
from server.models.users.merchants import Merchant
from server.models.auths.api_auth import MerchantAPI
from server.models.activities.jobs.agent_job import (
    AgentJob,
    AgentJobState
)
from server.models.notifications.notification_message import (
    Notification,
    NotificationState,
    NotificationType
)
from server.applications.customers.schemas.webhooks.webhook_schema import (
    AgentCompletedJob
)
from server.applications.customers.services.webhooks.webhook_service import (
    get_merchants_api_key,
    get_merchant_signature,
    get_merchant,
    create_notification_header,
    create_notification_message,
    NotificationMessageType
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Annotated
from datetime import datetime, timezone
from uuid import UUID

customer_api_webhook_router = APIRouter('/customer/webhooks', tags=['Router for the apis webhooks'])

"""Route for the webhook for the completed job"""
@customer_api_webhook_router.post('/requests')
async def update_customer_job(merchant_api_model:Annotated[MerchantAPI, Depends(get_merchants_api_key)],
                              merchant_signature:Annotated[str, Depends(get_merchant_signature)],
                              agent_completed_job:AgentCompletedJob,
                              session_db:Annotated[AsyncSession, Depends(get_relational_db_session)]):
    #checking the signature from client 
    if not merchant_api_model.check_signature(
        data=agent_completed_job.model_dump_json(),
        api_signature=merchant_signature
    ):
        raise HTTPException(
            status_code=400,
            detail='Invalid request. Signature\'s do not match.'
        )

    #casting job id str -> uuid 
    try:
        job_id = UUID(agent_completed_job.job_id)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail='Invalid id. Id passed is not in the right shape.'
        )

    #database query for the job 
    try:
        agent_job_query = await session_db.execute(select(AgentJob).where(and_(
            AgentJob.id == job_id
        )))
        agent_job = agent_job_query.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Database error. Unable to operate on the database.'
        )

    #check if query successful 
    if not agent_job:
        raise HTTPException(
            status_code=400,
            detail='Unable to locate the job from passed id.'
        )

    #updating attributes of the model 
    try:
        agent_job.job_state = AgentJobState.DONE
        agent_job.job_summary = agent_completed_job.job_action_summary
        await session_db.commit()
    except Exception:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail='Database error. Unable to operate on database.'
        )
    
    #creating the notifications for completed jobs 
    customer_notification_header = create_notification_header(agent_name=agent_job.hired_agent_name)
    customer_notification_message = create_notification_message(
        agent_job.hired_agent_name, 
        agent_job.job_name, 
        agent_job.job_summary,
        NotificationMessageType.CUSTOMER)
    
    #customer notification
    customer_notification = Notification(
        notification_header=customer_notification_header,
        notification_message=customer_notification_message,
        notification_state=NotificationState.UNREAD,
        notification_type=NotificationType.JOB_COMPLETED,
        customer_id=agent_job.customer_id,
        job_id=agent_job.id,
        created_at=datetime.now(timezone.utc)
    )

    #getting the merchant 
    merchant_notification_header = create_notification_header(agent_name=agent_job.hired_agent_name)
    merchant_notification_message = create_notification_message(
        agent_job.hired_agent_name,
        job_name=None,
        job_summary=None,
        message_type=NotificationMessageType.MERCHANT
    )
    try:
        merchant:Merchant = get_merchant(
            session_db=session_db,
            merchant_api_model=merchant_api_model
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Datebase error. Unable to operate on database.'
        )

    #merchant notification
    merchant_notification = Notification(
        notification_header=merchant_notification_header,
        notification_message=merchant_notification_message,
        notification_type=NotificationType.JOB_COMPLETED,
        notification_state=NotificationState.UNREAD,
        merchant_id=merchant.id,
        created_at=datetime.now(timezone.utc)
    )

    #mapping both notifications -> Postgres
    try:
        session_db.add(customer_notification)
        session_db.add(merchant_notification)
        await session_db.commit()
    except Exception:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail='Database error. Unable to operate database.'
        )

    return 