#File for the routes for the customer to hire the agent 
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.applications.customers.services.auth.auth_service import get_current_customer
from server.applications.customers.routes.pages.search.agent_search import customer_search_router
from server.app import (
    get_relational_db_session
)
from server.models.users.customers import Customer
from server.models.agents.agent import (
    Agent,
    AgentState
)
from server.models.agents.hired_agent import HiredAgent
from server.applications.customers.schemas.pages.search_schema import AgentContract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Annotated
from datetime import datetime, timezone
from uuid import UUID

"""Route for the customer to hire an agent"""
@customer_search_router.post('/agent/hire/{agent_id_str}')
async def customer_hire_agent(agent_id_str:str,
                              agent_contract:AgentContract,
                              session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                              customer:Annotated[Customer, Depends(get_current_customer)]):
     #casting agent id str -> uuid
    try:
        agent_id = UUID(agent_id_str) 
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=''
        )

    #database query for agent 
    try:
        agent_query = await session_db.execute(select(Agent).where(
            Agent.id == agent_id
        ))
        agent = agent_query.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=''
        )

    #check if agent was successfully retrieved 
    if not agent:
        raise HTTPException(
            status_code=400,
            detail=''
        )

    #creating the hired agent model 
    new_agent_hire = HiredAgent(
        name=agent.name,
        description=agent.description,
        agent_id=agent.id,
        customer_id=customer.id,
        agent_restrictions=agent_contract.agent_restrictions,
        agent_state=AgentState.ACTIVE,
        hired_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    #staging and committing newly hired agent 
    try:
        session_db.add(new_agent_hire)
        await session_db.commit()
    except Exception:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail=''
        )

    #returning response to client 
    return 
