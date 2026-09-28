#File for the server side event sent over to the client
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.sse import EventSourceResponse
from fastapi import Depends 
from server.app import get_notifications_events
from server.applications.customers.services.auth.auth_service import get_current_customer
from server.applications.customers.schemas.pages.notification_schemas import SSENotificationResponse
from server.models.users.customers import Customer
from server.config.apis import NotificationEvents
from typing import Annotated

#global router for customer noti server side events
customer_sse_router = APIRouter(prefix='/customer/notifications', tags=['Route for server side events'])

"""Route for server to send noti event to client"""
@customer_sse_router.get('/events', response_class=EventSourceResponse)
async def send_notification_event(customer:Annotated[Customer, Depends(get_current_customer)],
                                  events_manager:Annotated[NotificationEvents, Depends(get_notifications_events)]):
    async def stream_notifications():
        while True:
            customer_id = str(customer.id)
            await events_manager.event_wait(customer_id)
            notification_data = await events_manager.get_item(customer_id)
            customer_notification = notification_data.get('customer_noti') or {}
            yield SSENotificationResponse(
                notification_id=customer_notification.get('noti_id'),
                notification_header=customer_notification.get('noti_header'),
                notification_message=customer_notification.get('noti_message')
            )

    return EventSourceResponse(stream_notifications())
