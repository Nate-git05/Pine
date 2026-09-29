#File for the webhook schemas through the server
from pydantic import BaseModel, Field
from uuid import UUID

#Schema for the request body to update active job
class AgentCompletedJob(BaseModel):
    job_id:str
    job_action_summary:str

#Schema for job request webhook
class JobRequestWebhook(BaseModel):
    job_id:str
    request_name:str
    request_description:str
    current_job_summary:str

#Schema for the client webhook
class ClientWebhook(BaseModel):
    customer_id:UUID
    # This is the customer's HiredAgent row ID, used by AgentJob.hired_agent_id.
    agent_id:UUID
    agent_name:str = Field(max_length=50)

    job_name:str = Field(max_length=20)
    job_description:str = Field(max_length=100)
    job_price:int = Field(gt=0, le=2_147_483_647, description='Price in cents.')


class CachedClientJob(ClientWebhook):
    """A signed client-webhook job after Pine assigns its stable queue ID."""
    offer_id:UUID

#schema for the sse event
class AgentJobYield(BaseModel):
    offer_id:UUID
    agent_name:str
    agent_id:str
    job_name:str
    job_description_str:str
    job_price:float
