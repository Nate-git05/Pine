#File for the customer to search for the agent 
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.applications.customers.services.auth.auth_service import get_current_customer
from server.app import (
    get_relational_db_session,
    get_vector_database,
    get_openai_client
)
from server.applications.customers.schemas.pages.search_schema import (
    CustomerSearch
)
from server.models.users.customers import Customer
from server.models.agents.agent import (
    Agent,
    AgentState
)
from server.models.agents.hired_agent import HiredAgent
from server.config.database import (
    VectorDatabase,
    CollectionType
)
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncClient
from typing import Annotated

customer_search_router = APIRouter(prefix='/customer/search', tags=['Routes for the search navigation page.'])

"""Route for the customer to search for an agent"""
@customer_search_router.post('/agent/limit?={limit}')
async def customer_search_agent(customer_info:CustomerSearch,
                                session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                                vector_db:Annotated[VectorDatabase, Depends(get_vector_database)],
                                openai_client:Annotated[AsyncClient, Depends(get_openai_client)],
                                customer:Annotated[Customer, Depends(get_current_customer)],
                                agent_ids_seen:list,
                                limit:int=10
                                ):
    #vector database query ->
    try:
        #embedding the customer's query
        embedded_query = await vector_db.create_vector_embedding(openai_client, customer_info)

        payload_lst:list[dict] = await vector_db.retrieve(
            embeddings=embedded_query,
            limit=limit,
            collection_type=CollectionType.AGENT
        )

    except Exception:
        raise HTTPException(
            status_code=400,
            detail='API error. Please try to search again.'
        )