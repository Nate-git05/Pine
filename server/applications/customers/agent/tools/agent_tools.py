#File for building out the agent's tools 
from aiohttp import ClientSession
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
    HiredAgentResponse
)
from sqlalchemy import select, and_

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
                raise ValueError('')

            return HiredAgentResponse(
                agent_id=hired_agent.agent_id
            ).model_dump_json()

        #gets the agent from the hired agent 
        @tool
        async def get_hired_agent_url(agent_info:AgentInfo):

            pass

        #creates the job from customer -> agent 
        @tool
        async def create_hired_agents_job():
            pass

        #creates the conversation message for the agent 
        @tool
        async def create_hired_agents_convo():
            pass

        #creating the params request params 
        @tool
        def create_agents_request_params():
            pass

        #sends the agents job via request -> returns
        @tool 
        async def send_hired_agent_job():
            pass

        #sends the agent convo 
        @tool 
        async def send_hired_agent_convo():
            pass

    #returning the fucntions as a lst 
    return [
        get_customer_hired_agent,
        get_hired_agent_url,
        create_hired_agents_convo,
        create_hired_agents_convo,
        send_hired_agent_convo,
        send_hired_agent_job
    ]