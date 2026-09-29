#File for the route for the customer chatting with the agent
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.applications.customers.services.auth.auth_service import get_current_customer
from server.dependencies import (
    get_cache_db,
    get_server_agent,
    get_relational_db_session,
)
from server.models.users.customers import Customer
from server.models.agents.hired_agent import HiredAgent
from server.models.agents.agent import AgentState
from server.config.database import CacheDatabase
from server.applications.customers.agent.customer_agent import (
    PineAgent,
    AgentType,
    AgentMessage,
    AgentConfigurationError,
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
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

#global router for the home navigation page
customer_home_router = APIRouter(prefix='/customer/home', tags=['Routes for the app\'s home page'])

"""Route for the customer to communicate to their agent"""
@customer_home_router.post('/chat/{hired_agent_id_str}', response_model=AgentChatResponse)
async def chat_with_hired_agent(customer_info: AgentChatRequest,
                                hired_agent_id_str: str,
                                customer: Annotated[Customer, Depends(get_current_customer)],
                                session_db: Annotated[AsyncSession, Depends(get_relational_db_session)],
                                cache_db: Annotated[CacheDatabase, Depends(get_cache_db)],
                                pine_agent: Annotated[PineAgent, Depends(get_server_agent)]):
    # Parse the customer-specific hire ID from the chat path.
    try:
        hired_agent_id = UUID(hired_agent_id_str)
    except ValueError as error:
        raise HTTPException(status_code=400, detail='Invalid hired-agent ID.') from error

    # Verify that this customer owns an active hire before loading its history.
    try:
        hired_agent_query = await session_db.execute(select(HiredAgent).where(and_(
            HiredAgent.id == hired_agent_id,
            HiredAgent.customer_id == customer.id,
            HiredAgent.agent_state == AgentState.ACTIVE,
        )))
        hired_agent = hired_agent_query.scalar_one_or_none()
    except Exception as error:
        raise HTTPException(status_code=500, detail='Unable to verify this hired agent.') from error

    if not hired_agent:
        raise HTTPException(status_code=404, detail='No active hired agent was found for this customer.')

    # Separate router and tooling histories for this customer and hired agent.
    cache_key_router = f'{customer.id}/{hired_agent.id}/router'
    cache_key_tooling = f'{customer.id}/{hired_agent.id}/tooling'

    try:
        router_context = await pine_agent.get_context(
            cache_key=cache_key_router,
            agent_type=AgentType.ROUTER,
            cache_db=cache_db,
        )

        # Give the router the current message and its prior classifications.
        router_message = create_router_agent_message(
            previous_context=router_context,
            customer_message=customer_info.customer_message,
        )

        message_type = await pine_agent.run_router_agent(router_message=router_message)

        # Save this routing turn so future messages can use its context.
        router_turn = return_router_agent_context(
            customer_message=customer_info.customer_message,
            message_type=message_type,
        )
        await pine_agent.store_context(
            cache_key=cache_key_router,
            agent_type=AgentType.ROUTER,
            cache_value=router_turn,
            cache_db=cache_db,
        )

        tooling_agent_context = await pine_agent.get_context(
            cache_key=cache_key_tooling,
            agent_type=AgentType.TOOLING,
            cache_db=cache_db,
        )

        tooling_agent_message = create_tooling_agent_message_str(
            previous_context=tooling_agent_context,
            hired_agent_id=str(hired_agent.id),
            customer_message=customer_info.customer_message,
        )
        agent_message = AgentMessage(
            message_type=message_type,
            message=tooling_agent_message,
        )

        agent_response = await pine_agent.run_tooling_agent(agent_message=agent_message)

        # Store only serializable conversation text in the tooling history.
        tooling_turn = return_tooling_agent_context(
            customer_message=customer_info.customer_message,
            agent_response=agent_response.response,
        )
        await pine_agent.store_context(
            cache_key=cache_key_tooling,
            agent_type=AgentType.TOOLING,
            cache_value=tooling_turn,
            cache_db=cache_db,
        )

        return AgentChatResponse(response=agent_response.response)
    except AgentConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail='The agent could not process this message. Please try again.',
        ) from error
