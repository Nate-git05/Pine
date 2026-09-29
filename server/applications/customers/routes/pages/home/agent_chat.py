#File for the route for the customer chatting with the agent
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.applications.customers.services.auth.auth_service import get_current_customer
from server.dependencies import (
    get_relational_db_session,
    get_cache_db,
    get_server_agent
)
from server.models.users.customers import Customer
from server.config.database import CacheDatabase
from server.applications.customers.agent.customer_agent import (
    PineAgent,
    AgentType
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

#global router for the home navigation page
customer_home_router = APIRouter(prefix='/customer/home', tags=['Routes for the app\'s home page'])

"""Route for the customer to communicate to their agent"""
@customer_home_router.post('/chat/{hired_agent_name}/{hired_agent_id_str}')
async def chat_with_hired_agent(customer_info,
                                hired_agent_name:str, 
                                hired_agent_id_str:str,
                                customer:Annotated[Customer, Depends(get_current_customer)],
                                cache_db:Annotated[CacheDatabase, Depends(get_cache_db)],
                                pine_agent:Annotated[PineAgent, Depends(get_server_agent)]):
    try:
        #getting router context 
        cache_key = f'{str(customer.id)}/{hired_agent_name}/router'
        router_context = await pine_agent.get_context(
            cache_key=cache_key,
            agent_type=AgentType.ROUTER,
            cache_db=cache_db
        )

        #building the message for the router agent 
    pass 
