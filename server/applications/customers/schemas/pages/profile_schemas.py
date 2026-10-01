#File for the schemas for the customer profile page
from pydantic import BaseModel
from enum import Enum, StrEnum
from datetime import datetime
import strawberry

"""Strawberry schema for the graphql routes"""
class CustomerProfile(BaseModel):
    #customer attributes
    customer_name:str = None
    customer_email:str = None
    customer_number:str = None

    #payment attribute
    card_type:str | None = None
    active_card_last4:str | None = None
    expire_date:str | None = None

    #agent/jobs attributes
    number_of_agents:int = None
    jobs_completed:int = None

#Schema for customer hire/fire agent
class AgentContractResponse(BaseModel):
    response:str

#Schema for the customer's hired-agent details
class HiredAgentProfile(BaseModel):
    id: str
    name: str
    description: str
    state: str
    rating: float
    agent_imgicon_key: str
    hired_at: datetime
    price_per_job: int
    agent_restrictions: list[str] | None = None
    agent_abilities: list[str]

#Schema for the type of integration
class EmailIntegrationType(StrEnum):
    GMAIL='gmail'
    YAHOOO='yahoo'
    OUTLOOK='outlook'

#Schema for the returned google url
class GoogleRedirectURL(BaseModel):
    redirect_url:str

#Schema for the resqust for google redirect
class GoogleRedirectInfo(BaseModel):
    code:str
    state:str
    scope:str

#Schema for the integration response
class GmailIntegrationResponse(BaseModel):
    response:str

"""GraphQL schema for the customer's hired agents."""
@strawberry.enum
class HiredAgentState(Enum):
    ACTIVE = 'active'
    FIRED = 'fired'


@strawberry.type
class CustomerHiredAgent:
    id: str = None
    name: str = None
    description: str = None
    state: HiredAgentState = None
    rating: float = 0.0


@strawberry.type
class CustomerHiredAgentsResponse:
    status_code: int = None
    response: str | None = None
    hired_agents: list[CustomerHiredAgent] | None = None
