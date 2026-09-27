#File for the graphql routes for the activity navigation page 
import strawberry
from strawberry import (
    Schema,
    Info
)
from strawberry.fastapi import GraphQLRouter
from server.models.users.customers import Customer
from server.models.activities.jobs.job_request import (
    AgentJobRequest,
    JobRequestState
)
from server.models.activities.jobs.agent_job import (
    AgentJob,
    AgentJobState
)
from server.models.activities.transactions.job_payments import JobPayments
from server.applications.customers.services.auth.auth_service import get_customer_context
from server.applications.customers.schemas.pages.activities_schema import (
    HTTPException,
    JobRequestResponse,
    JobReturnedResponse,
    PaymentsReturnedResponse
)
from server.applications.customers.services.pages.activity_service import (
    job_reqest_lst_returned,
    jobs_returned_lst,
    get_customer_payments_lst
)
from sqlalchemy import select, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

"""Client side query for the activity page"""
@strawberry.type
class ActivityPageQuery:
    #field for the client side query -> job requests 
    @strawberry.field()
    async def job_requests(self, customer_context:Info, limit:int=5):
        try:
            customer:Customer = customer_context.context.get('customer')
            session_db:AsyncSession = customer_context.context.get('database_session')
            cursor:bool = customer_context.context.get('cursor')
            last_request_made:datetime = customer_context.context.get('last_made')
        except Exception:
            return HTTPException(
                status_code=400,
                detail='Unable to authenticate the session.'
            )

        #database query -> job requests 
        try:
            if cursor:
                job_requests_query = await session_db.execute(select(AgentJobRequest).where(and_(
                    AgentJobRequest.customer_id == customer.id,
                    AgentJobRequest.job_request_state == JobRequestState.NOT_HANDLED,
                    AgentJobRequest.request_made_at > last_request_made
                )).order_by(desc(AgentJobRequest.request_made_at)).limit(limit=limit))
            else:
                job_requests_query = await session_db.execute(select(AgentJobRequest).where(and_(
                    AgentJobRequest.customer_id == customer.id,
                    AgentJobRequest.job_request_state == JobRequestState.NOT_HANDLED
                )).order_by(desc(AgentJobRequest.request_made_at)))
            customer_job_requests = job_requests_query.scalars().all() #query returned -> python lst
        except Exception:
            return HTTPException(
                status_code=500,
                detail='Database error. Please try selecting the job requests again'
            )

        #check if there are any pending 
        if not customer_job_requests:
            return JobRequestResponse(
                status_code=200,
                response='There arent\'s currently any job requests.',
                cursor=None,
                last_request_date=None
            )

        #getting the list of job requests returned
        request_lst_returned = job_reqest_lst_returned(
            job_request_lst=customer_job_requests
        )

        #returning response to the client
        return JobRequestResponse(
            status_code=200,
            response=None,
            returned_job_requests=request_lst_returned,
            cursor=True,
            last_request_date=customer_job_requests[-1].request_made_at
        )

    #field for getting the active jobs 
    @strawberry.field
    async def active_jobs(self, customer_context:Info, limit:int=5):
        #getting the validated customer info
        try:
            customer:Customer = customer_context.context.get('customer')
            session_db:AsyncSession = customer_context.get('database_session')  
            cursor:bool = customer_context.context.get('cursor')
            last_active_job = customer_context.context.get('last_active_job')
        except Exception:
            raise HTTPException(
                status_code=400,
                detail='Invalid request. Please try selecting the active jobs again.'
            )

        #database query for -> customers active jobs 
        try:
            if cursor:
                active_jobs_query = session_db.execute(select(AgentJob).where(and_(
                    AgentJob.customer_id == customer.id,
                    AgentJob.job_state == AgentJobState.ACTIVE,
                    AgentJob.assigned_at > last_active_job
                )).order_by(asc(AgentJob.assigned_at)).limit(limit=limit))
            else:
                active_jobs_query = await session_db.execute(select(AgentJob).where(and_(
                    AgentJob.customer_id == customer.id,
                    AgentJob.job_state == AgentJobState.ACTIVE
                )).order_by(asc(AgentJob.assigned_at))) #sorts by the earliest job
            customer_active_jobs = active_jobs_query.scalars().all()
        except Exception:
            raise HTTPException(
                status_code=500,
                detail='Database error. Please try selecting the active jobs again.'
            )

        #checking if any active jobs 
        if not customer_active_jobs:
            return JobReturnedResponse(
                status_code=200,
                response='There aren\'t any current active jobs.',
                jobs_returned=None,
                cursor=None,
                last_job_date=None
            )

        #getting the list of returned active jobs
        returned_active_jobs = jobs_returned_lst(
            jobs_lst=customer_active_jobs,
            job_state=AgentJobState.ACTIVE
        )

        #returning response to the client
        return JobReturnedResponse(
            status_code=200,
            response=None,
            jobs_returned=returned_active_jobs,
            cursor=True,
            last_job_date=customer_active_jobs[-1].assigned_at
        )

    #field for the client side query -> completed jobs 
    @strawberry.field
    async def completed_jobs(self, customer_context:Info, limit:int=5):
        #retrieving the customers context
        try:
            customer:Customer = customer_context.context.get('customer')
            session_db:AsyncSession = customer_context.context.get('database_session')
            cursor:bool = customer_context.context.get('cursor')
            last_completed_payment_date:datetime = customer_context.context.get('last_id_seen')
        except Exception:
            return HTTPException(
                status_code=400,
                detail='Unable to retrieve customer context. Please try selecting the completed jobs again.'
            )

        #database query -> completed jobs 
        try:
            #check based on cursor 
            if cursor:
                completed_jobs_query = await session_db.execute(select(AgentJob).where(and_(
                    AgentJob.customer_id == customer.id,
                    AgentJob.job_state == AgentJobState.DONE,
                    AgentJob.completed_at < last_completed_payment_date
                )).order_by(desc(AgentJob.completed_at)).limit(limit=limit))
            else:
                completed_jobs_query = await session_db.execute(select(AgentJob).where(and_(
                    AgentJob.customer_id == customer.id,
                    AgentJob.job_state == AgentJobState.DONE
                )).order_by(desc(AgentJob.completed_at)).limit(limit=limit))

            customer_completed_jobs = completed_jobs_query.scalars().all() #gets the completed jobs in lst
        except Exception:
            return HTTPException(
                status_code=500,
                detail='Database error. Please try selectign completed jobs again.'
            )

        #check if the customer has any completed jobs 
        if not customer_completed_jobs:
            return JobReturnedResponse(
                status_code=200,
                response='There aren\'t any completed jobs.',
                cursor=None,
                last_request_date=None
            )

        #getting lst of the returned completed jobs 
        returned_complete_jobs = jobs_returned_lst(
            jobs_lst=customer_completed_jobs,
            job_state=AgentJobState.DONE
        )

        #return response to the client
        return JobReturnedResponse(
            status_code=200,
            response=None,
            jobs_returned=returned_complete_jobs,
            cursor=True,
            last_job_date=customer_completed_jobs[-1].completed_at #getting last job at end of lst
        )

    #client side query for the jobs transactions 
    @strawberry.field 
    async def customer_job_payments(self, customer_context:Info, limit:int=5):
        #getting the customer context info 
        try:
            customer:Customer = customer_context.context.get('customer')
            session_db:AsyncSession = customer_context.context.get('database_session')
            cursor:bool = customer_context.context.get('cursor')
            last_payment_made:datetime = customer_context.context.get('last_date')
        except Exception:
            return HTTPException(
                status_code=400,
                detail='Unable to locate customer\'s context. Please try selecting again.'
            )

        #database query for the customer transactions
        try:
            if cursor:
                payments_query = await session_db.execute(select(JobPayments).where(and_(
                    JobPayments.customer_id == customer.id,
                    JobPayments.paid_at > last_payment_made
                )).order_by(desc(JobPayments.paid_at)).limit(limit=limit))
            else:
                payments_query = await session_db.execute(select(JobPayments).where(
                    JobPayments.customer_id == customer.id
                ).order_by(desc(JobPayments.paid_at)).limit(limit=limit))
            payments = payments_query.scalars().all()
        except Exception:
            return HTTPException(
                status_code=500,
                detail='database error. Please try selecting again.'
            )

        #check if the customer has any payments made 
        if not payments:
            return PaymentsReturnedResponse(
                status_code=200,
                response='There haven\'t been any payments made.',
                payments_returned=None,
                cursor=None,
                last_payment_date=False
            )

        #getting the lst of payments returned to server
        payments_returned_lst = get_customer_payments_lst(
            customer_payments=payments
        )

        #returning response to client
        return PaymentsReturnedResponse(
            status_code=200,
            response=None,
            payments_returned=payments_returned_lst,
            cursor=True,
            last_payment_date=payments[-1].paid_at
        )


#Configuring the GraphQL router 
activity_page_schema = Schema(query=ActivityPageQuery) #query schema 
activity_page_graphql_router = GraphQLRouter(
    prefix='/customer/activity',
    schema=activity_page_schema,
    context_getter=get_customer_context
)