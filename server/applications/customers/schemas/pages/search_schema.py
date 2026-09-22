#Schema file for the search page -> customers looking for agents
from pydantic import (
    BaseModel,
    field_validator,
    model_validator
)

"""Schema for the request/response in for search page"""
class CustomerSearch(BaseModel):
    search_request:str = None 

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