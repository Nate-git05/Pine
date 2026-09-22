#Schema file for the search page -> customers looking for agents
from pydantic import (
    BaseModel,
    field_validator,
    model_validator
)

"""Schema for the request/response in for search page"""
class CustomerSearch(BaseModel):
    search_request:str = None 
    agent_ids_seen:list[str] = None 

    #validating the search field
    @field_validator('search_request')
    @classmethod
    def search_check(cls, request:str) -> str:
        request = request.strip() #stripping leading/ending whitespace 
        if not request:
            raise ValueError('Please enter a term to start searching.')

        return request 

    #validating the schema model 
    @model_validator(mode='after')
    def customer_search_check(self):
        if not self.search_request:
            raise ValueError('Please enter a term to start searching.')

        return self #returning the schema

#schema for the individual agent returned 
class AgentsReturned(BaseModel):
    agent_id:str = None 
    agent_name:str = None 
    agent_description:str = None 

#schema for the list of agents returned  
class AgentReturnedList(BaseModel):
    response:str | None = None 
    returned_agents:list[AgentsReturned] | None = None 
    agent_seen_lst:list[str] = None 

#schema for the response for returned agent
class ReturnedAgent(BaseModel):
    #agent information
    agent_id:str = None 
    agent_imgicon_key:str = None 
    agent_name:str = None 
    agent_description:str = None 
    agent_skills:list = None

#schema for returning the merchat parcial info -> merchant hosts agent
class AgentMerchantInfo(BaseModel):
    merchant_id:str = None 
    merchant_imgicon_key:str = None

#schema for the response returned from route 
class SearchedAgentResponse(BaseModel):
    returned_info:dict[str] = None 