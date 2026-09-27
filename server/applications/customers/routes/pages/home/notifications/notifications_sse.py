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
import json

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

        #looping through the notis in queue 
        try:
            for noti in events_manager.async_queue:
                if noti.get('customer_id') == str(customer.id):
                    customer_data:dict = json.loads(noti)
                    break
        except Exception as err:
            raise err

        return customer_data #returning the customer data 

    #getting the customer data 
    try:
        customer_data:dict = await get_notification_data()
        notification_data:dict = customer_data.get('customer_noti')
    except Exception:
        raise HTTPException(
            status_code=400,
            detail='Unable to retrieve the customer notification data.'
        )

    #pydantic model for the response 
    returned_noti = SSENotificationResponse(
        notification_id=notification_data.get('noti_id'),
        notification_header=notification_data.get('noti_header'),
        notification_message=notification_data.get('noti_message')
    )
    
    yield returned_noti #yielding the response to the client 