#File for the Tools scheams -> tool fucntions params 
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID

"""Schemas for querying the relational database"""
#Argument schemas -> query the hired agent 
class HiredAgentInfo(BaseModel):
    customer_id:UUID
    hired_agent_id:UUID

#Arguement schemas -> query the agent from hired agent
class AgentInfo(BaseModel):
    agent_id:UUID

#Argument schema -> check an email connected to the customer
class CustomerEmailInfo(BaseModel):
    customer_id:UUID
    email_name:EmailStr

#Response schemas -> returned agent id 
class HiredAgentResponse(BaseModel):
    hired_agent_id:UUID
    job_price:int
    agent_id:UUID
    agent_name:str
    #The hire's configured abilities describe the work the agent can take on.
    agent_abilities:list[str]
    agent_restrictions:list[str] | None = None

#Response schemas -> returns the agents url 
class ReturnAgentURL(BaseModel):
    agent_url:str

"""Schemas for the agents request"""
#Arguement schema -> job request 
class AgentJob(BaseModel):
    customer_id:UUID
    # The client webhook expects its agent_id to be the HiredAgent row ID.
    agent_id:UUID
    agent_name:str = Field(max_length=50)
    job_name:str = Field(max_length=20)
    job_description:str = Field(max_length=100)
    job_price:int = Field(gt=0, le=2_147_483_647, description='Price in cents.')

#Argument schema -> conversation request
class AgentConversation(BaseModel):
    conversation_name:str
    defined_customer_request:str

#Response schema for the agent -> conversation
class AgentRequest(BaseModel):
    pine_signature:str
    agent_job:AgentJob | None = None 
    conversation_data:AgentConversation | None = None

"""Schemas for the request"""
#params for the agents request 
class DataForRequest(BaseModel):
    request_url:str 
    headers:dict[str, str]
    data:str

#Schema for the response to the agent 
class RequestResponse(BaseModel):
    accepted:bool
    status_code:int | None = None
    response:str
