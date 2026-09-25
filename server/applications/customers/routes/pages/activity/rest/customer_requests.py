#File for the REST methods for the activities page 
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.applications.customers.services.auth.auth_service import get_current_customer
from server.app import get_relational_db_session
from server.models.users.customers import Customer
from server.models.activities.jobs.job_request import AgentJobRequest
from server.applications.customers.schemas.pages.activities_schema import (
    IndividualJobRequest,
    CustoemrResquestAnswer
)
from server.applications.customers.services.pages.activity_service import get_agent_url
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
        hired_agent_name=job_request.hired_agent_name,
        requested_at=job_request.request_made_at.strftime("%I:%M %p")
    )

    return job_request_returned #request returned to client 

"""Route for customer to answer the request"""
@customer_activity_router.post('/request/answer/{request_id_str}')
async def customer_answer_requst(request_id_str:str,
                                 customer_info:CustoemrResquestAnswer,
                                 session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                                 customer:Annotated[Customer, Depends(get_current_customer)]):
    #cast request id str -> uuid 
    try:
        request_id = UUID(request_id_str)
    except Exception:
        raise HTTPException()

    #database query -> job request
    try:
        request_query = await session_db.execute(select(AgentJobRequest).where(and_(
            AgentJobRequest.id == request_id,
            AgentJobRequest.customer_id == customer.id
        )))
        customer_request = request_query.scalar_one_or_none()
    except Exception:
        raise HTTPException()

    #check if request was queried 
    if not customer_request:
        raise HTTPException()

    #updating the model with the response 
    try:
        customer_request.customer_request_response = customer_info.customer_response
        await session_db.commit()
    except Exception:
        await session_db.rollback()
        raise HTTPException()

    #getting the hired agent info -> getting the hired agent info for request 
    try:
        agent_url = await get_agent_url(session_db)
    except Exception:
        raise HTTPException()
    
    #sending sending the response for request -> agent
    