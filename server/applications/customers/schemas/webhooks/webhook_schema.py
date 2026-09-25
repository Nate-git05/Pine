#File for the webhook schemas through the server
from pydantic import BaseModel

#Schema for the request body to update active job
class AgentCompletedJob(BaseModel):
    job_id:str = None 
    job_action_summary:str = None 