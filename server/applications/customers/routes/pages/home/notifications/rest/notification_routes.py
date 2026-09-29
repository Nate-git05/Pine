#File for the REST methods for the notifications
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.applications.customers.services.auth.auth_service import get_current_customer
from server.dependencies import (
    get_relational_db_session
)
from server.models.users.customers import Customer
from server.models.notifications.notification_message import (
    Notification,
    NotificationState
)
from server.applications.customers.schemas.pages.home_schemas import (
    ReturnedNotification,
    NotificationsCleared
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from typing import Annotated
from uuid import UUID
from datetime import datetime, timezone

#global router for notifications
customer_notification_router = APIRouter(prefix='/customer/notifications', tags=['Router for the notifications'])

"""Route to get specific notification"""
@customer_notification_router.get('/{notification_id_str}', response_model=ReturnedNotification)
async def get_customer_notification(notification_id_str:str,
                                    customer:Annotated[Customer, Depends(get_current_customer)],
                                    session_db:Annotated[AsyncSession, Depends(get_relational_db_session)]):
    #casting the str notification id -> uuid
    try:
        notification_id = UUID(notification_id_str)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail='Invalid notification ID.'
        )

    #database query for the notification
    try:
        notification_query = await session_db.execute(select(Notification).where(and_(
            Notification.id == notification_id,
            Notification.customer_id == customer.id
        )))
        notification = notification_query.scalar_one_or_none() #returns none if not found
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Unable to load this notification.'
        )

    #check if able to find notification
    if not notification:
        raise HTTPException(
            status_code=404,
            detail='Notification was not found.'
        )

    #updating the notification state
    try:
        if notification.notification_state == NotificationState.UNREAD:
            notification.notification_state = NotificationState.READ
            notification.read_at = datetime.now(timezone.utc)
            await session_db.commit()
    except Exception:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail='Unable to update this notification.'
        )

    #pydantic model for the notification
    returned_notification = ReturnedNotification(
        notification_header=notification.notification_header,
        notification_message=notification.notification_message,
        notification_type=notification.notification_type,
        notification_date=notification.created_at.strftime("%b %d, %Y")
    )

    return returned_notification #returning the notification to the client

"""Route for the customer current set of notifications"""
@customer_notification_router.patch('/clear', response_model=NotificationsCleared)
async def clear_notifications(customer:Annotated[Customer, Depends(get_current_customer)],
                              session_db:Annotated[AsyncSession, Depends(get_relational_db_session)]):
    #database query for the customers notifications
    try:
        notifications_query = await session_db.execute(select(Notification).where(and_(
            Notification.customer_id == customer.id,
            Notification.notification_state == NotificationState.UNREAD
        )))
        notifications = notifications_query.scalars().all()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Unable to load your notifications.'
        )

    #check if there are notifications
    if not notifications:
        return NotificationsCleared(
            response='There aren\'t any unread notifications.'
        )

    #transaction to update the notifications
    try:
        #updating all unread notifications for this customer
        await session_db.execute(update(Notification).where(and_(
            Notification.customer_id == customer.id,
            Notification.notification_state == NotificationState.UNREAD
        )).values(
                notification_state=NotificationState.READ,
                read_at=datetime.now(timezone.utc)
            ))
        await session_db.commit()
    except Exception:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail='Unable to clear your notifications.'
        )

    return NotificationsCleared(
        response='Notifications were successfully cleared.'
    )