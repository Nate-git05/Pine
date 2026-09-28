#File for the helper functions used in the activity routes 
from server.applications.customers.schemas.pages.activities_schema import (
    ReturnedJobRequest,
    JobReturned,
    PaymentReturned
)
from server.models.users.merchants import Merchant
from server.models.auths.api_auth import MerchantAPI
from server.models.activities.jobs.job_request import AgentJobRequest
from server.models.activities.jobs.agent_job import (
    AgentJob,
    AgentJobState
)
from server.models.agents.agent import Agent
from server.models.agents.hired_agent import HiredAgent
from server.models.activities.transactions.job_payments import JobPayments
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

#Helper function takes the job requests lst -> packages in pydantic model 
def job_reqest_lst_returned(job_request_lst:list[AgentJobRequest]) -> list:
    job_requests_returned = [] #lst to store the requests 

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

#function to return the active jobs as a list 
def jobs_returned_lst(jobs_lst:list[AgentJob], job_state:AgentJobState):
    returned_jobs = []

    #looping through the lst of active jobs 
    for active_job in jobs_lst:
        job_returned = JobReturned(
            agent_job_id=str(active_job.id),
            agent_job_name=active_job.job_name,
            agent_job_description=active_job.job_description,
        )

        #check for the job state -> Done/Active
        if job_state == AgentJobState.ACTIVE:
            job_returned.created_at = f'Created at: {active_job.assigned_at.strftime("%I:%M %p")}'
        else:
            job_returned.completed_at = f'Completed on: {active_job.completed_at.strftime("%m/%d/%Y")}'

        returned_jobs.append(job_returned) #appending the job to the list

    return returned_jobs

#helper function to return the lst of payments
def get_customer_payments_lst(customer_payments:list[JobPayments]):
    returned_payments = [] #list to return the customer payments

    #looping through the job payments 
    for payment in customer_payments:
        returned_payment = PaymentReturned(
            payment_id=str(payment.id),
            job_name=payment.job_name,
            payment_amount=(payment.job_price / 100), #returns correct decimal price
            paid_at=f'Paid at: {payment.paid_at.strftime("%m/%d/%Y")}'
        )

        returned_payments.append(returned_payment) #appending the payment to list

    return returned_payments #returning the list of payments

#Helper function to get the agents hosted url 
async def get_agent_url(session_db:AsyncSession, request:AgentJobRequest):
    try:
        hired_agent_query = await session_db.execute(select(HiredAgent).where(and_(
            HiredAgent.id == request.hired_agent_id
        )))
        hired_agent = hired_agent_query.scalar_one_or_none()

        #check if hired agent was found
        if not hired_agent:
            raise Exception('Unable to locate the hired agent.')

        #getting the agent from the hired agent 
        agent_query = await session_db.execute(select(Agent).where(
            Agent.id == hired_agent.agent_id
        ))
        agent = agent_query.scalar_one_or_none()
    except Exception as error:
        raise error

    #check if agent was queried
    if not agent:
        raise Exception('Unable to locate the agent from hired agent id.')

    return agent.agents_webhook_url #returning the agents url for webhook

#helper function to get the merchants signature -> and sign it 
async def get_merchant_signature(session_db:AsyncSession, request:AgentJobRequest, data:str):
    try:
        #database query for the hired agent 
        hired_agent_query = await session_db.execute(select(HiredAgent).where(
            HiredAgent.id == request.hired_agent_id
        ))
        hired_agent = hired_agent_query.scalar_one_or_none()

        #check for hired agent query 
        if not hired_agent:
            raise Exception('Unable to locate the hired agent from the query.')

        #database query for the agent 
        agent_query = await session_db.execute(select(Agent).where(
            Agent.id == hired_agent.agent_id
        ))
        agent = agent_query.scalar_one_or_none()

        #check if agent was queried 
        if not agent:
            raise Exception('Unable to locate the agent from the query.')

        #query for the merchant 
        merchant_query = await session_db.execute(select(Merchant).where(
            Merchant.id == agent.merchant_id
        ))
        merchant = merchant_query.scalar_one_or_none()

        #check if merchant was successfully queried 
        if not merchant:
            raise Exception('Unable to locate the merchant from the query.')

        #getting the merchants api
        merchant_api_query = await session_db.execute(select(MerchantAPI).where(
            MerchantAPI.merchant_id == merchant.id
        ))
        merchant_api = merchant_api_query.scalar_one_or_none()
    except Exception as error:
        raise error 

    #check if merchant api 
    if not merchant_api:
        raise Exception('Unable to locate the merchant api from the query.')

    return merchant_api.get_merchant_signature(
        data=data
    )
