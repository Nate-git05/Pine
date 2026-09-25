#File for the REST methods for the activities page 
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.applications.customers.services.auth.auth_service import get_current_customer
from server.app import get_relational_db_session
from server.models.users.customers import Customer
from server.models.activities.jobs.agent_job import (
    AgentJob,
    AgentJobState
)
from server.models.activities.jobs.job_request import AgentJobRequest
from server.models.activities.transactions.job_payments import JobPayments
from server.applications.customers.schemas.pages.activities_schema import (
    IndividualJobRequest,
    IndividualJob,
    CustomerJobRating
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Annotated
from uuid import UUID

customer_activity_router = APIRouter('/customer/activity') #router for the activity page REST methods

"""Route to get the agents job request for the customer"""
@customer_activity_router.get('/jobs/requests/{request_id_str}', response_model=IndividualJobRequest)
async def get_customer_job_request(request_id_str:str,
                                   session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                                   customer:Annotated[Customer, Depends(get_current_customer)]):
    #casting request id str -> UUID
    try:
        request_id = UUID(request_id_str)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail='Invalid id. Please try selecting the request again.'
        )

    #database query -> job request 
    try:
        job_request_query = await session_db.execute(select(AgentJobRequest).where(and_(
            AgentJobRequest.id == request_id,
            AgentJobRequest.customer_id == customer.id
        )))
        job_request = job_request_query.scalar_one_or_none() #getting the first request found 
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=''
        )

    #check if the request queried 
    if not job_request:
        raise HTTPException(
            status_code=400,
            detail=''
        )

    #building pydantic model for job request 
    job_request_returned = IndividualJobRequest(
        request_id=str(job_request.id),
        request_name=job_request.request_name,
        request_description=job_request.request_description,
        agent_current_job_summary=job_request.job_summary,
        hired_agent_id=str(job_request.hired_agent_id),
        hired_agent_name=job_request.hired,
        requested_at=job_request.request_made_at.strftime("%I:%M %p")
    )

    return job_request_returned #request returned to client 

"""Route to get the customer done/active job"""
@customer_activity_router.get('/jobs/{job_id_str}', response_model=IndividualJob)
async def get_customer_job(job_id_str:str,
                           session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                           customer:Annotated[Customer, Depends(get_current_customer)]):
    #casting the job id str -> uuid 
    try:
        job_id = UUID(job_id_str) 
    except Exception:
        raise HTTPException(
            status_code=400,
            detail='Invalid id. Please try selecting the job again.'
        )

    #database query for the agents job 
    try:
        job_query = await session_db.execute(select(AgentJob).where(and_(
            AgentJob.id == job_id,
            AgentJob.customer_id == customer.id
        )))
        job = job_query.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Database error. Pleasetry selecting the job again.'
        )

    #check if job was queried
    if not job:
        raise HTTPException(
            status_code=400,
            detail='Invalid id. Unable to locate the job.'
        )
    #building pydantic model for job returned 
    returned_job = IndividualJob(
        job_id=str(job.id),
        job_name=job.job_name,
        job_description=job.job_description,
        job_price=job.job_rating if job.job_state else None,
        hired_agent_id=job.hired_agent_id,
        hired_agent_name=job.hired_agent_name,
        assigned_at=job.assigned_at if job.job_state == AgentJobState.ACTIVE else None,
        completed_at=job.completed_at if job.job_state == AgentJobState.DONE else None 
    )

    return returned_job #returning the job to the client 

"""Route to post rating for customer"""
@customer_activity_router.post('/job/rating/{job_id_str}')
async def post_customer_job_rating(job_id_str:str,
                                   session_db:Annotated[AsyncSession, Depends(get_relational_db_session)])