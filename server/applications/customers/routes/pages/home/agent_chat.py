#File for the route for the customer chatting with the agent
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.applications.customers.services.auth.auth_service import get_current_customer
from server.dependencies import (
    get_cache_db,
    get_server_agent
)
from server.models.users.customers import Customer
from server.config.database import CacheDatabase
from server.applications.customers.agent.customer_agent import (
    PineAgent,
    AgentType,
    AgentMessage
)
from server.applications.customers.schemas.pages.home_schemas import (
    AgentChatRequest,
    AgentChatResponse
)
from server.applications.customers.services.pages.home_service import (
    create_router_agent_message,
    create_tooling_agent_message_str,
    return_router_agent_context,
    return_tooling_agent_context
)
from typing import Annotated

#global router for the home navigation page
customer_home_router = APIRouter(prefix='/customer/home', tags=['Routes for the app\'s home page'])

"""Route for the customer to communicate to their agent"""
@customer_home_router.post('/chat/{hired_agent_name}/{hired_agent_id_str}', response_model=AgentChatResponse)
async def chat_with_hired_agent(customer_info:AgentChatRequest,
                                hired_agent_name:str, 
                                hired_agent_id_str:str,
                                customer:Annotated[Customer, Depends(get_current_customer)],
                                cache_db:Annotated[CacheDatabase, Depends(get_cache_db)],
                                pine_agent:Annotated[PineAgent, Depends(get_server_agent)]):
    try:
        #getting router context 
        cache_key_router = f'{str(customer.id)}/{hired_agent_name}/router'
        router_context = await pine_agent.get_context(
            cache_key=cache_key_router,
            agent_type=AgentType.ROUTER,
            cache_db=cache_db
        )

        #building the message for the router agent 
        router_message = create_router_agent_message(
            previous_context=router_context,
            customer_message=customer_info.customer_message
        )

        #running the message through the router agent 
        message_type = pine_agent.run_router_agent(
            router_message=router_message
        )

        #appending context to the router agent 
        new_added_context = return_router_agent_context(
            customer_message=customer_info.customer_message,
            message_type=message_type
        )
        await pine_agent.store_context(
            cache_key=cache_key_router,
            agent_type=AgentType.ROUTER,
            cache_value=new_added_context,
            cache_db=cache_db
        )

        #getting the tooling agent context
        cache_key_tooling = f'{str(customer.id)}/{hired_agent_name}/tooling'
        tooling_agent_context = await pine_agent.get_context(
            cache_key=cache_key_tooling,
            agent_type=AgentType.TOOLING,
            cache_db=cache_db
        )

        #building out the tooling agents message str
        tooling_agent_message = create_tooling_agent_message_str(
            previous_context=tooling_agent_context,
            hired_agent_id=hired_agent_id_str,
            customer_message=customer_info.customer_message
        )
        agent_message = AgentMessage(
            message_type=message_type,
            message=tooling_agent_message
        )

        #running the message through the tooling agent 
        response = await pine_agent.run_tooling_agent(
            agent_message=agent_message
        )

        #updating the agents context 
        new_added_context = return_tooling_agent_context(
            customer_message=customer_info.customer_message,
            agent_response=response
        )
        await pine_agent.store_context(
            cache_key=cache_key_tooling,
            agent_type=AgentType.TOOLING,
            cache_value=new_added_context,
            cache_db=cache_db
        )

        #returning response to the client
        return AgentChatResponse(
            response=response
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=''
        )