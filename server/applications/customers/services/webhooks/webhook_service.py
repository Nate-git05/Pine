#Service file for the helper functions in webhook routes
from fastapi.requests import Request
from fastapi.exceptions import HTTPException
from server.models.auths.api_auth import MerchantAPI
from server.models.users.merchants import Merchant
from server.models.activities.jobs.agent_job import AgentJob
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from enum import StrEnum
from uuid import UUID

"""Dependency function to retrieve the merchants api key"""
#dependency function auht the merchant with api key 
async def get_merchants_api_model(request:Request):
    #getting the database session 
    try:
        database_session:AsyncSession = request.app.state.relational_database 
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Unable to retrieve application info.'
        )

    #getting the api key from the request
    try:
        merchant_api_key_str = request.headers.get('Api-Key')
        #check if there is a api key
        if not merchant_api_key:
            raise HTTPException(
                status_code=400,
                detail='Unable to locate the api key in request.'
            )
        
        merchant_api_key = UUID(merchant_api_key_str) #casting api key str -> uuid 

        #database query for the merchant
        merchant_api_query = await database_session.execute(select(MerchantAPI).where(
            MerchantAPI.api_key == merchant_api_key
        ))
        merchant_api_model = merchant_api_query.scalar_one_or_none() #gets the first api model found

        #check if model was queired 
        if not merchant_api_model:
            raise HTTPException(
                status_code=400,
                detail='Unable to validate api key.'
            )

        #returning the merchant api model to route
        return merchant_api_model
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Database error. Request failed.'
        )

#dependency function to get the signature of the request
def get_merchant_signature(request:Request):
    signature = request.headers.get('Signature')
    if not signature:
        raise HTTPException(
            status_code=400,
            detail='Unable to locate the signature in the request.'
        )

    return signature #returning the merchants signature

"""Helper functions for the routes"""
async def get_merchant(session_db:AsyncSession, merchant_api_model:MerchantAPI):
    #database query for mercahnt
    try:
        merchant_query = await session_db.execute(select(Merchant).where(
            Merchant.id == merchant_api_model.merchant_id
        ))
        merchant = merchant_query.scalar_one_or_none()
    except Exception as error:
        raise error 

    #check if merchant exists 
    if not merchant:
        raise Exception('Unable to locate the merchant SQL model.')

    return merchant #returning found merchant

"""Enum for denoting who the message is for"""
class NotificationMessageType(StrEnum):
    CUSTOMER='customer'
    MERCHANT='merchant'

#helper functions to create notification message 
def create_job_notification_message(agent_name:str, job_name:str | None,  message_type:NotificationMessageType):
    match message_type:
        case NotificationMessageType.CUSTOMER:
            return f'Hey your agent {agent_name} just completed the job {job_name}\
                     assigned to it. Check it out in your activity page to view it.'
        
        case NotificationMessageType.MERCHANT:
            return f'Congrats your agent had just completed a job for a customer.'

#helper function to create notification header
def create_job_notification_header(agent_name:str):
    return f'{agent_name} has just completed a job.'

#helper function -> gets the agent for the request 
async def get_request_job(session_db:AsyncSession, job_id_str:str) -> AgentJob:
    #casting job id str -> uuid 
    try:
        job_id = UUID(job_id_str) 
    except Exception as error:
        raise error 

    #database query for the job
    try:
        agent_job_query = await session_db.execute(select(AgentJob).where(
            AgentJob.id == job_id
        ))
        agent_job = agent_job_query.scalar_one_or_none()
    except Exception as error:
        raise error 

    #check if job was queried 
    if not agent_job:
        raise Exception('Unable to locate the job at the job id.')

    return agent_job #returning the agents job

#helper functions to create notification header
def create_request_notification_header(agent_name:str):
    return f'{agent_name} has a request for a job.'

#helper function to create notification message 
def create_request_notification_message(agent_name:str, job_name:str):
    return f'Hey your agent {agent_name} has made a request for the job\
             {job_name}. Check your activity page to view the request.'