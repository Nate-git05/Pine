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
    agent_id:UUID

#Response schemas -> returned agent id 
class HiredAgentResponse(BaseModel):
    agent_id:UUID

#Response schemas -> returns the agents url 
class ReturnAgentURL(BaseModel):
    agent_url:str

"""Schemas for the agents job creation"""