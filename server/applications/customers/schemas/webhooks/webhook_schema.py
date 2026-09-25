#File for the webhook schemas through the server
from pydantic import BaseModel

#Schema for the request body to update active job
class AgentCompletedJob(BaseModel):
    job_id:str = None 
    job_action_summary:str = None 

#Schema for job request webhook
class JobRequestWebhook(BaseModel):
    job_id:str = None 
    request_name:str = None 
    request_description:str = None 
    current_job_summary:str = None 