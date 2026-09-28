#File for the webhook schemas through the server
from pydantic import BaseModel, Field

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
    customer_id:str
    agent_id:str
    agent_name:str

    job_name:str
    job_description:str
    job_price:int = Field(gt=0, description='Price in cents.')

#schema for the sse event
class AgentJobYield(BaseModel):
    offer_id:str
    agent_name:str
    agent_id:str
    job_name:str
    job_description_str:str
    job_price:float
