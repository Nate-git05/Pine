#Schema file for the home page for the cusotmer 
from pydantic import (
    BaseModel,
    field_validator,
    model_validator
)
import strawberry
from datetime import datetime
from server.models.notifications.notification_message import NotificationType
import re

#Schema for the returned stripe payment
class ReturnedPayments(BaseModel):
    payment_id:str | None = None 
    payment_last4:str | None  = None 
    payment_card_type:str | None = None
    expires_at:str = None 

#schema for the response model 
class ReturnedPaymentsList(BaseModel):
    response:str | None = None
    payments_lst:list[ReturnedPayments] | None = None

#Schema for the agents request
class AgentsJobRequest(BaseModel):
    customer_id:str = None 
    job_id:str = None 
    job_name:str = None 
    job_description:str = None
    agent_restrictions:list[str] | None = None

#schema for the Payment response 
class PaymentResponse(BaseModel):
    response:str = None 

#Schema for response from success/failed url for stripe 
class StripePaymentResponse(BaseModel):
    response:str = None 

#Schema for the response for notification
class ReturnedNotification(BaseModel):
    notification_header:str = None 
    notification_message:str = None 
    notification_type:str = None
    notification_date:str = None 

#Schema for the response -> Notifications been cleared
class NotificationsCleared(BaseModel):
    response:str = None 

#Schema for the customer request for agent chat
class AgentChatRequest(BaseModel):
    customer_message:str | None = None 

    #validating the field 
    @field_validator('customer_message')
    @classmethod
    def message_check(message:str) -> str:
        message = message.strip() #stripping/leading whitespace 
        if not message:
            raise ValueError('')

        #checking the contents of the message 
        pattern = r''
        if re.match(pattern, message):
            raise ValueError('')
        
        return message

    #validating the model 
    @model_validator(mode='after')
    def customer_chat_check(self):
        if not self.customer_message:
            raise ValueError('')

        return self #returns the schema

#Schema for the response from chat route 
class AgentChatResponse(BaseModel):
    response:str = None 

"""GraphQl schemas for responses"""
#Schema for the individual notification returned
@strawberry.type 
class IndividualNotification:
    noti_id:str = None 
    noti_header:str = None 
    noti_message:str = None
    noti_type:NotificationType = None
    notification_date:str = None 

#Schema for the notification response from graphql route 
@strawberry.type 
class NotificationResponse:
    status_code:int = None 
    returned_notifications:list[IndividualNotification] | None = None 
    response:str | None = None
    last_notification_id_seen:datetime | None = None 
    cursor:bool | None = None