#File for the graphql route for the notifications
import strawberry
from strawberry import (
    Info,
    Schema
)
from strawberry.fastapi import GraphQLRouter
from server.applications.customers.services.auth.auth_service import get_customer_context
from server.models.users.customers import Customer
from server.models.notifications.notification_message import (
    Notification,
    NotificationState
)
from server.applications.customers.schemas.pages.home_schemas import NotificationResponse
from server.applications.customers.services.pages.home_service import get_notification_returned
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from datetime import datetime

"""Query object for the client side query"""
@strawberry.type
class NotificationsQuery:
    @strawberry.field
    async def customer_notifications(
        self,
        customer_info:Info,
        limit:int=5
    ) -> NotificationResponse:
        #getting context from the query request
        try:
            customer:Customer = customer_info.context.get('customer')
            session_db:AsyncSession = customer_info.context.get('database_session')
            cursor:bool = customer_info.context.get('cursor')
            last_notification_seen:datetime = customer_info.context.get('last_seen')
        except Exception:
            return NotificationResponse(
                status_code=400,
                response='Unable to load your notification session.',
                cursor=False
            )

        #keeping the notification page size within a reasonable range
        limit = max(1, min(limit, 50))

        #database query for the customer notifications
        try:
            #if cursor exists -> query from last id seen
            if cursor and last_notification_seen:
                customer_notifications_query = await session_db.execute(select(Notification).where(and_(
                    Notification.customer_id == customer.id,
                    Notification.notification_state == NotificationState.UNREAD,
                    Notification.created_at < last_notification_seen
                )).order_by(desc(Notification.created_at)).limit(limit=limit + 1))
            else:
                customer_notifications_query = await session_db.execute(select(Notification).where(and_(
                    Notification.customer_id == customer.id,
                    Notification.notification_state == NotificationState.UNREAD
                )).order_by(desc(Notification.created_at)).limit(limit=limit + 1))

            customer_notifications = customer_notifications_query.scalars().all()
        except Exception:
            return NotificationResponse(
                status_code=500,
                response='Unable to load your notifications.',
                cursor=False
            )

        #checking if the notifications returned
        if not customer_notifications:
            return NotificationResponse(
                status_code=200,
                returned_notifications=None,
                response='There aren\'t any notifications currently.',
                last_notification_id_seen=None,
                cursor=False
            )

        #checking if another page exists, then returning the requested limit
        has_more = len(customer_notifications) > limit
        customer_notifications = customer_notifications[:limit]

        #getting the returned lst of notifications
        returned_notifications = get_notification_returned(
            customer_notifications=customer_notifications
        )

        #returning response to client side
        return NotificationResponse(
            status_code=200,
            returned_notifications=returned_notifications,
            response=None,
            last_notification_id_seen=customer_notifications[-1].created_at,
            cursor=has_more
        )

"""Creating the GraphQL router for query"""
notification_schema = Schema(query=NotificationsQuery)
notifications_page_router = GraphQLRouter(
    schema=notification_schema,
    path='/customer/notifications',
    context_getter=get_customer_context
)
