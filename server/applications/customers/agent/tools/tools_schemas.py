#File for the Tools scheams -> tool fucntions params 
from pydantic import BaseModel
from uuid import UUID

"""Schemas for querying the relational database"""
#Argument schemas -> query the hired agent 
class HiredAgentInfo(BaseModel):
    customer_id:UUID
    hired_agent_id:UUID

#Arguement schemas -> query the agent from hired agent
class AgentInfo(BaseModel):
    hired_agent_job_price:int
    agent_id:UUID

#Response schemas -> returned agent id 
class HiredAgentResponse(BaseModel):
    job_price:int
    agent_id:UUID

#Response schemas -> returns the agents url 
class ReturnAgentURL(BaseModel):
    agent_url:str

"""Schemas for the agents request"""
#Arguement schema -> job request 
class AgentJob(BaseModel):
    customer_id:str
    job_name:str
    job_description:str
    job_price:int

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
    headers:dict
    data:str

#Schema for the response to the agent 
class RequestResponse(BaseModel):
    response:str 