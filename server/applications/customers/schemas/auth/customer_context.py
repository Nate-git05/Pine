#File for the customer GraphQL request context schema
import json
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator

"""Schema for the cursor values in a GraphQL request"""
class CustomerContextVariables(BaseModel):
    model_config = ConfigDict(extra='allow')

    cursor:bool | None = None
    last_id_seen:datetime | None = None
    last_date:datetime | None = None
    last_seen:datetime | None = None

"""Schema for the customer GraphQL request body"""
class CustomerContextRequest(BaseModel):
    model_config = ConfigDict(extra='allow')

    query:str | None = None
    operationName:str | None = None
    variables:CustomerContextVariables | None = None
    cursor:bool | None = None
    last_id_seen:datetime | None = None
    last_date:datetime | None = None
    last_seen:datetime | None = None

    #loading the variables when GraphQL sends them as a query string
    @field_validator('variables', mode='before')
    @classmethod
    def load_variables(cls, request_variables):
        if isinstance(request_variables, str):
            try:
                request_variables = json.loads(request_variables)
            except Exception:
                return None

        return request_variables
