#File for the webhook for the agents made request
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.applications.customers.routes.webhooks.apis.job_webhook import customer_api_webhook_router
from server.app import (
    get_relational_db_session,
    get_notifications_events
)
from server.applications.customers.services.auth.auth_service import get_current_customer
from server.models.auths.api_auth import MerchantAPI
from server.models.notifications.notification_message import (
    Notification,
    NotificationType,
    NotificationState
)
from server.models.activities.jobs.job_request import (
    AgentJobRequest,
    JobRequestState
)
from server.config.apis import NotificationEvents
from server.applications.customers.schemas.webhooks.webhook_schema import JobRequestWebhook
from server.applications.customers.services.webhooks.webhook_service import (
    get_merchant_signature,
    get_merchants_api_model,
    get_request_job,
    create_request_notification_header,
    create_request_notification_message
)
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import Annotated

"""Route for the job request to create agents job request"""
@customer_api_webhook_router.post('/requests')
async def create_cusotmer_job_request(merchant_api_model:Annotated[MerchantAPI, Depends(get_merchants_api_model)],
                                      merchant_signature:Annotated[str, Depends(get_merchant_signature)],
                                      agent_request:JobRequestWebhook,
                                      session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                                      events_manager:Annotated[NotificationEvents, Depends(get_notifications_events)]):
    #checking the signature of the webhook
    if not merchant_api_model.check_signature(
        data=agent_request.model_dump_json(),
        api_signature=merchant_signature
    ):
        raise HTTPException(
            status_code=400,
            detail='Invalid signature. Request failed'
        )

    #getting job assigned to this request 
    try:
        agent_job = await get_request_job(
            session_db=session_db,
            job_id_str=agent_request.job_id
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Database error. Unable to operate on the database.'
        )

    #creating new job request model 
    new_job_request = AgentJobRequest(
        job_summary=agent_request.current_job_summary,
        request_name=agent_request.request_name,
        request_description=agent_request.request_description,
        job_request_state=JobRequestState.NOT_HANDLED,
        hired_agent_id=agent_job.hired_agent_id,
        agent_job_id=agent_job.id,
        customer_id=agent_job.customer_id,
        agent_hired_name=agent_job.hired_agent_name,
        request_made_at=datetime.now(timezone.utc)
    )

    #creating the customer's notification
    notification_header = create_request_notification_header(
        agent_name=new_job_request.hired_agent_name
    )
    notification_message = create_request_notification_message(
        agent_name=new_job_request.hired_agent_name,
        job_name=agent_job.job_name
    )
    customer_notification = Notification(
        notification_header=notification_header,
        notification_message=notification_message,
        notification_type=NotificationType.REQUEST_MADE,
        notification_state=NotificationState.UNREAD,
        customer_id=new_job_request.customer_id,
        created_at=datetime.now(timezone.utc)
    )

    #mapping the new SQL objects to Posgres
    try:
        session_db.add(new_job_request) 
        session_db.add(customer_notification)
        await session_db.commit() 
    except Exception:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail='Database error. Unable to operate on database.'
        )

    #building out data for sse event
    notification_data = {
        'customer_id':str(customer_notification.customer_id),
        'customer_noti':{
            'noti_id':str(customer_notification),
            'noti_header':customer_notification.notification_header,
            'noti_message':customer_notification.notification_message
        }
    }

    #starting the sse event for notification to client side 
    try:
        await events_manager.event_set(
            data=notification_data
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Server error. Unable to wake event.'
        )
