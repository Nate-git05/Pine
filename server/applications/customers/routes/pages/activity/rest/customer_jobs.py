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
from server.applications.customers.schemas.pages.activities_schema import (
    IndividualJobRequest,
    IndividualJob,
    CustomerJobRating,
    RatingResponse
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Annotated
from uuid import UUID

customer_activity_router = APIRouter(prefix='/customer/activity') #router for the activity page REST methods

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
        job_price=(job.job_price / 100),
        job_summary=job.job_summary,
        hired_agent_id=str(job.hired_agent_id),
        hired_agent_name=job.hired_agent_name,
        assigned_at=job.assigned_at if job.job_state == AgentJobState.ACTIVE else None,
        completed_at=job.completed_at if job.job_state == AgentJobState.DONE else None 
    )

    return returned_job #returning the job to the client 

"""Route to post rating for customer"""
@customer_activity_router.post('/job/rating/{job_id_str}', response_model=RatingResponse)
async def post_customer_job_rating(job_id_str:str,
                                   customer_info:CustomerJobRating,
                                   session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                                   customer:Annotated[Customer, Depends(get_current_customer)]):
    #casting the id str -> uuid 
    try:
        job_id = UUID(job_id_str)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail='Invalid id. Please entering the rating again.'
        )

    #database query for the job 
    try:
        job_query = await session_db.execute(select(AgentJob).where(and_(
            AgentJob.id == job_id,
            AgentJob.customer_id == customer.id
        )))
        agent_job = job_query.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Database error. Please try entering the rating again.'
        )

    #check if the job was queried
    if not agent_job:
        raise HTTPException(
            status_code=400,
            detail='Unable to locate the job. Please try entering the rating again.'
        )

    if agent_job.job_state != AgentJobState.DONE:
        raise HTTPException(status_code=409, detail='Only completed jobs can be rated.')
    if agent_job.job_rating is not None:
        raise HTTPException(status_code=409, detail='This job has already been rated.')

    #updating the SQL model 
    try:
        agent_job.job_rating = customer_info.job_rating
        await session_db.commit()
    except Exception:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail='Database error. Please try entering the rating again.'
        )

    #response to the client 
    return RatingResponse(
        response='Thank you for your rating!'
    )
