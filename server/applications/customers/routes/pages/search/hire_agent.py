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
from server.models.notifications.notification_message import (
    Notification,
    NotificationType,
    NotificationState
)
from server.applications.customers.schemas.pages.search_schema import (
    AgentContract,
    AgentContractResponse
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Annotated
from datetime import datetime, timezone
from uuid import UUID

"""Route for the customer to hire an agent"""
@customer_search_router.post('/agent/hire/{agent_id_str}', response_model=AgentContractResponse)
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
            detail='Invalid id. Please try hiring the agent again.'
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
            detail='Database error. Please try hiring the agent again.'
        )

    #check if agent was successfully retrieved 
    if not agent:
        raise HTTPException(
            status_code=400,
            detail='Unable to locate agent. Please try hiring the agent again.'
        )

    #creating the hired agent model 
    new_agent_hire = HiredAgent(
        name=agent.name,
        description=agent.description,
        price_per_job=agent.agent_price_per_job,
        agent_id=agent.id,
        customer_id=customer.id,
        agent_restrictions=agent_contract.agent_restrictions,
        agent_state=AgentState.ACTIVE,
        agent_imgicon_key=agent.imgicon_storage_key,
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
            detail='Database error. Please try hiring the agent again.'
        )

    #creating notification for the merchant 
    new_merchant_notification = Notification(
        notification_header=f'New Agent Hire!',
        notification_message=f'Congratulations {customer.name} just hired your agent {agent.name}.',
        notification_type=NotificationType.AGENT_HIRED,
        notification_state=NotificationState.UNREAD,
        merchant_id=agent.merchant_id,
        created_at=datetime.now(timezone.utc)
    )

    #staging and commiting new notification
    try:
        session_db.add(new_merchant_notification)
        await session_db.commit()
    except Exception:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail='Database error. Having trouble hiring the agent. Please try again.'
        ) 

    #returning response to client 
    return AgentContractResponse(
        hired_agent_id=str(new_agent_hire.id),
        response=f'The agent {new_agent_hire.name} was successfully hired.'
    )

"""Route for the customer to fire the agent."""
@customer_search_router.patch('/agent/fire/{agent_hire_id}')
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
            HiredAgent.customer_id == customer.id
        )))
        hired_agent = hired_agent_query.scalar_one_or_none()

        #check if the agent hired row returned 
        if not hired_agent:
            raise HTTPException(
                status_code=400,
                detail='Unable to locate the agent. Please try again to fire the agent.'
            )
        #updating the agent's state
        hired_agent.agent_state = AgentState.FIRED
        await session_db.commit() #commiting changes made to database
    except Exception:
        await session_db.rollback() #uncommiting the changes made
        raise HTTPException(
            status_code=500,
            detail='Database error. Please try to fire the agent again.'
        )