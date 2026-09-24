#File for the helper functions used in the activity routes 
from server.applications.customers.schemas.pages.activities_schema import (
    ReturnedJobRequest
)
from server.models.activities.jobs.job_request import AgentJobRequest

#Helper function takes the job requests lst -> packages in pydantic model 
def job_reqest_lst_returned(job_request_lst:list[AgentJobRequest]) -> list:
    job_requests_returned = []

    #looping through the lst of job requests 
    for request in job_request_lst:
        returned_request = ReturnedJobRequest(
            request_id=str(request.id),
            request_name=request.request_name,
            request_description=request.request_description,
            rrequest_created_at=f'Request made at: {request.request_made_at.strftime("%I:%M %p")}'
        )

        job_requests_returned.append(returned_request) #appending the request to the lst 

    return job_requests_returned #returning the request lst