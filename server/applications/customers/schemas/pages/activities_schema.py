#File for the schemas for the customer activities page 
import strawberry
from pydantic import BaseModel

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

"""Schemas for the agent jobs"""
#individual job returned in lst
@strawberry.type 
class JobReturned:
    agent_job_id:str = None 
    agent_job_name:str = None 
    agent_job_description:str = None 
    created_at:str = None

@strawberry.type
class JobReturnedResponse:
    status_code:int = None
    response:str | None = None 
    jobs_returned:list[JobReturned] | None = None 