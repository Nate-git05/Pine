#Schema file for the home page for the cusotmer 
from pydantic import BaseModel

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

#schema for the Payment response 
class PaymentResponse(BaseModel):
    response:str = None 

#Schema for response from success/failed url for stripe 
class StripePaymentResponse(BaseModel):
    response:str = None 