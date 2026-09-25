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
    async def get_notification_data() -> dict:
        #continous loop while queue is empty
        while not events_manager.async_queue:
            events_manager.event_wait() #event waits 

        data:dict = events_manager.get_item()
        return data 

    events_manager.event_wait() #waiting the event again
    notification_data:dict = get_notification_data() #getting data from the inner function

    #pydantic model for the response 
    returned_noti = SSENotificationResponse(
        notification_id=notification_data.get('noti_id'),
        notification_header=notification_data.get('noti_header'),
        notification_message=notification_data.get('noti_message')
    )
    
    yield returned_noti #yielding the response to the client 