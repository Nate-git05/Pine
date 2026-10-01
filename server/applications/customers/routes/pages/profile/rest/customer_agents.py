from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.applications.customers.services.auth.auth_service import get_current_customer
from server.dependencies import (
    get_relational_db_session
)
from server.applications.customers.routes.pages.profile.rest.customer_profile import customer_profile_router
from server.applications.customers.services.pages.profile_service import (
    get_customer_hired_agent,
)
from server.models.users.customers import Customer
from server.models.agents.hired_agent import (
    HiredAgent,
    AgentState
)
from server.applications.customers.schemas.pages.profile_schemas import (
    AgentContractResponse,
    HiredAgentProfile
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Annotated
from uuid import UUID

"""Route to get one of the customer's hired agents by its id."""
@customer_profile_router.get('/agents/{hired_agent_id}', response_model=HiredAgentProfile)
async def get_customer_hired_agent_route(
    hired_agent_id: UUID,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session_db: Annotated[AsyncSession, Depends(get_relational_db_session)]
):
    # Query by both IDs so customers can only retrieve their own hired agents.
    try:
        customer_hired_agent = await get_customer_hired_agent(
            session_db=session_db,
            customer_id=customer.id,
            hired_agent_id=hired_agent_id
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Unable to load this hired agent. Please try again.'
        )

    if not customer_hired_agent:
        raise HTTPException(
            status_code=404,
            detail='Unable to locate this hired agent for your account.'
        )

    hired_agent, job_rating = customer_hired_agent

    return HiredAgentProfile(
        id=str(hired_agent.id),
        name=hired_agent.name,
        description=hired_agent.description,
        state=str(hired_agent.agent_state),
        rating=job_rating,
        agent_imgicon_key=hired_agent.agent_imgicon_key,
        hired_at=hired_agent.hired_at,
        price_per_job=hired_agent.price_per_job,
        agent_restrictions=hired_agent.agent_restrictions,
        agent_abilities=hired_agent.agent_abilities
    )


"""Route for the customer to fire the agent."""
@customer_profile_router.patch('/agents/fire/{agent_hire_id}')
async def customer_fire_agent(agent_hire_id:str,
                              session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                              customer:Annotated[Customer, Depends(get_current_customer)]):
    #casting the id str -> uuid
    try:
        hired_agent_id = UUID(agent_hire_id)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail='Invalid id. Please try to fire the agent again.'
        )

    try:
        #database query for the hired agent
        hired_agent_query = await session_db.execute(select(HiredAgent).where(and_(
            HiredAgent.id == hired_agent_id,
            HiredAgent.customer_id == customer.id,
            HiredAgent.agent_state == AgentState.ACTIVE
        )))
        hired_agent = hired_agent_query.scalar_one_or_none()

        #check if the agent hired row returned
        if not hired_agent:
            raise HTTPException(
                status_code=404,
                detail='Unable to locate an active hired agent for this customer.'
            )
        #updating the agent's state
        hired_agent.agent_state = AgentState.FIRED
        await session_db.commit() #commiting changes made to database
    except HTTPException:
        await session_db.rollback()
        raise
    except Exception:
        await session_db.rollback() #uncommiting the changes made
        raise HTTPException(
            status_code=500,
            detail='Database error. Please try to fire the agent again.'
        )

    return AgentContractResponse(
        response='Agent was successfully removed from your active agents.'
    )

"""Route for customer to rehire the agent"""
@customer_profile_router.patch('/agents/hire/{hired_agent_id_str}')
async def customer_rehire_agent(hired_agent_id_str:str,
                                customer:Annotated[Customer, Depends(get_current_customer)],
                                session_db:Annotated[AsyncSession, Depends(get_relational_db_session)]):
    #cast str id -> uuid
    try:
        hired_agent_id = UUID(hired_agent_id_str)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail='Invalid hired-agent ID. Please try again.'
        )

    #database query for the customer agent
    try:
        customer_hired_agent_query = await session_db.execute(select(HiredAgent).where(and_(
            HiredAgent.id == hired_agent_id,
            HiredAgent.customer_id == customer.id,
            HiredAgent.agent_state == AgentState.FIRED
        )))
        customer_hired_agent = customer_hired_agent_query.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Unable to look up this hired agent. Please try again.'
        )

    #check if query returned agent
    if not customer_hired_agent:
        raise HTTPException(
            status_code=404,
            detail='Unable to locate a fired hired agent for this customer.'
        )

    #updating the hired agent
    try:
        customer_hired_agent.agent_state = AgentState.ACTIVE
        await session_db.commit()
    except Exception:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail='Unable to reactivate this agent. Please try again.'
        )

    return AgentContractResponse(
        response='Agent was successfully added to your active agents.'
    )
