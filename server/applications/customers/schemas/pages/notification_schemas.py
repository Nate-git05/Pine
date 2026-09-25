#File for the schemas for the notifications page 
from pydantic import BaseModel

#Schema for the noti data returned from sse response 
class SSENotificationResponse(BaseModel):
    notification_id:str = None
    notification_header:str = None
    notification_message:str = None