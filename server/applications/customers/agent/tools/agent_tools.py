#File for building out the agent's tools 
from aiohttp import (
    ClientSession,
    ClientError
)
from agents.decorators import tool
from server.models.agents.hired_agent import HiredAgent
from server.models.agents.agent import (
    Agent,
    AgentState
)
from server.config.database import RelationalDatabase
from server.applications.customers.agent.tools.tools_schemas import (
    HiredAgentInfo, 
    AgentInfo,
    ReturnAgentURL,
    HiredAgentResponse,
    AgentJob,
    AgentConversation,
    AgentRequest,
    DataForRequest,
    RequestResponse
)
from sqlalchemy import select, and_
import hmac 
import hashlib

"""Function returns the lst of agent tools"""
async def retrieve_agents_tools(relational_db:RelationalDatabase,
                                http_client:ClientSession,
                                pine_server_key:str,
                                webhook_url:str):
    #creating the inner function tools
    async for session in relational_db.get_db():
        #gets the customers hired_agent 
        @tool
        async def get_customer_hired_agent(hired_agent_info:HiredAgentInfo):
            #error messages returned to agent 
            database_query_error = ''
            unsuccessful_query_error = ''

            #database query for the customers hired agent 
            try:
                hired_agent_query = await session.execute(select(HiredAgent).where(and_(
                    HiredAgent.id == hired_agent_info.hired_agent_id,
                    HiredAgent.customer_id == hired_agent_info.customer_id,
                    HiredAgent.agent_state == AgentState.ACTIVE
                )))
                hired_agent = hired_agent_query.scalar_one_or_none()
            except Exception:
                return database_query_error

            #check if hired agent found 
            if not hired_agent:
                return unsuccessful_query_error

            return HiredAgentResponse(
                job_price=hired_agent.price_per_job,
                agent_id=hired_agent.agent_id
            ).model_dump_json()

        #gets the agent from the hired agent 
        @tool
        async def get_hired_agent_url(agent_info:AgentInfo):
            database_query_error = ''
            unsuccessful_query_error = ''

            #database query for the agent -> hired agent 
            try:
                agent_query = await session.execute(select(Agent).where(and_(
                    Agent.id == agent_info.agent_id,
                    Agent.agent_state == AgentState.ACTIVE
                )))
                agent = agent_query.scalar_one_or_none()
            except Exception:
                return database_query_error

            #check if agent was queried 
            if not agent:
                return unsuccessful_query_error

            #returning the agents webhook url
            return ReturnAgentURL(
                agent_url=agent.agents_webhook_url
            ).model_dump_json() 

        #tool to get pine signature -> job request
        @tool
        def pine_request_data(agent_data:AgentJob | AgentConversation):
            hashing_error = ''
            try:
                pine_signature = hmac.new(
                    key=pine_server_key.encode('utf-8'),
                    msg=agent_data.model_dump_json().encode('utf-8'),
                    digestmod=hashlib.sha256
                )
            except Exception:
                return hashing_error

            #returning the agent request data
            return AgentRequest(
                pine_signature=pine_signature,
                agent_job=agent_data if type(agent_data) == AgentJob else None,
                conversation_data=agent_data if type(agent_data) == AgentConversation else None
            ).model_dump_json()

        #tool to create the request data 
        @tool
        def create_agent_job_request(agent_url:str, agent_data:AgentRequest):
            #request header
            request_header = {
                'Content-type':'application/json',
                'Signature':agent_data.pine_signature
            }

            #dumping data -> json
            data = agent_data.agent_job.model_dump_json()

            #returning info to client 
            return DataForRequest(
                request_url=agent_url,
                headers=request_header,
                data=data
            ).model_dump_json()

        #request for new job 
        @tool
        def create_agent_conversation_request(agent_data:AgentRequest):
            #request header
            request_header = {
                'Content-type':'application/json',
                'Signature':agent_data.pine_signature
            }

            #dumping data -> json
            data = agent_data.conversation_data.model_dump_json()

            #returning info to client 
            return DataForRequest(
                request_url=webhook_url,
                headers=request_header,
                data=data
            ).model_dump_json()

        #tool for customer to send over request 
        @tool
        async def send_agent_request(agent_request_data:DataForRequest):
            #error messages 
            sending_request_error = ''
            invalid_status_code_error = ''

            #sending request over to customer
            try:
                async with http_client.post(
                    url=agent_request_data.request_url,
                    headers=agent_request_data.headers,
                    data=agent_request_data.data
                ) as url_response:
                    #checking status code of request 
                    if url_response.status >= 300 or url_response.status < 200:
                        return invalid_status_code_error

                    #getting string response from 
                    response = await url_response.text()
                    return response 
            except ClientError:
                pass
            except Exception:
                return sending_request_error

    #returning the fucntions as a lst 
    return [
        get_customer_hired_agent,
        get_hired_agent_url,
        pine_request_data,
        create_agent_job_request,
        create_agent_conversation_request,
        send_agent_request
    ]