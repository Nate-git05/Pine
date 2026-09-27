#File for the schemas for the customer activities page 
import strawberry
from pydantic import (
    BaseModel,
    field_validator,
    model_validator
)
from datetime import datetime
import re

"""Custom exception for the graphql routes"""
#Strawberry defined Http exception
@strawberry.type
class HTTPException:
    status_code:int = None
    detail:str = None 

"""Schemas for the agents job requests"""
#Strawberry field for the independent job request
@strawberry.type
class ReturnedJobRequest:
    request_id:str = None 
    request_name:str = None
    request_description:str = None  
    rrequest_created_at:str = None 
    
#strawberry field for job request response 
@strawberry.type
class JobRequestResponse:
    status_code:int = None 
    response:str | None = None
    returned_job_requests:list[ReturnedJobRequest] | None = None
    cursor:bool | None = None 
    last_request_date:datetime | None = None 

"""Schemas for the agent jobs"""
#individual job returned in lst
@strawberry.type 
class JobReturned:
    agent_job_id:str = None 
    agent_job_name:str = None 
    agent_job_description:str = None 
    created_at:str | None = None
    completed_at:str | None = None

@strawberry.type
class JobReturnedResponse:
    status_code:int = None
    response:str | None = None 
    jobs_returned:list[JobReturned] | None = None 
    cursor:bool | None = None 
    last_job_date:datetime | None = None 

"""Schemas for the customers payments"""
#individual payment in the lst
@strawberry.type
class PaymentReturned:
    payment_id:str = None
    job_name:str = None
    payment_amount:float = None 
    paid_at:str = None

#response from the graphql field
@strawberry.type
class PaymentsReturnedResponse:
    status_code:int = None 
    response:str | None = None
    payments_returned:list[PaymentReturned] | None = None 
    cursor:bool | None = None 
    last_payment_date:datetime | None = None 

"""Schemas for the pydantic models"""
#schema for the individual job request returned 
#pydantic model for the individual job request pulled up 
class IndividualJobRequest(BaseModel):
    #request attributes
    request_id:str = None
    request_name:str = None 
    request_description:str = None 

    #agent attributes 
    agent_current_job_summary:str = None 
    hired_agent_id:str = None 
    hired_agent_name:str = None 

    #audit attributes
    requested_at:str = None 

#Schema for the individual job returned
class IndividualJob(BaseModel):
    job_id:str = None
    job_name:str = None 
    job_description:str = None 
    job_price:float = None
    job_rating:int | None = None
    job_summary:str = None

    #agent atributes 
    hired_agent_id:str = None
    hired_agent_name:str = None 

    #audit attributes 
    assigned_at:str | None = None
    completed_at:str | None = None

#Schema for the customer to answer the request
class CustomerRequestAnswer(BaseModel):
    customer_response:str = None 

    #validating the field
    @field_validator('customer_response')
    @classmethod
    def response_check(cls, response:str) -> str:
        response.strip() #striping leading/ending whitespace 
        if not response:
            raise ValueError('Request response cannot be empty.')

        #checking if the response has any spaces 
        pattern = r''
        if re.match(pattern, response):
            raise ValueError('Request response cannot contain any spaces.')

        return response  #response returned 

    #validating the model 
    @model_validator(mode='after')
    def response_schema_check(self):
        if not self.customer_response:
            raise ValueError('Response needed for the request.')

        return self #returning the schema

#Schema for the customer rating for job
class CustomerJobRating(BaseModel):
    job_rating:float = None 

#Schema for the response for the job rating 
class RatingResponse(BaseModel):
    response:str = None 