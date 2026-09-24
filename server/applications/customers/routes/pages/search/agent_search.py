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
    CustomerSearch,
    AgentReturnedList,
    AgentInfo,
    AgentMerchantInfo,
    AgentResponse
)
from server.models.users.customers import Customer
from server.models.users.merchants import Merchant
from server.models.agents.agent import Agent
from server.config.database import (
    VectorDatabase,
    CollectionType
)
from server.applications.customers.services.pages.search_service import (
    retrieve_queryied_agents,
    update_agent_ids_lst,
    get_agents_rating
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from openai import AsyncClient
from typing import Annotated
from uuid import UUID

customer_search_router = APIRouter(prefix='/customer/search', tags=['Routes for the search navigation page.'])

"""Route for the customer to search for an agent"""
@customer_search_router.post('/agents?={limit}', response_model=AgentReturnedList)
async def customer_search_agent(customer_info:CustomerSearch,
                                vector_db:Annotated[VectorDatabase, Depends(get_vector_database)],
                                openai_client:Annotated[AsyncClient, Depends(get_openai_client)],
                                customer:Annotated[Customer, Depends(get_current_customer)],
                                limit:int=10
                                ):
    #vector database query ->
    try:
        #embedding the customer's query
        embedded_query = await vector_db.create_vector_embedding(openai_client, customer_info)

        #check if cursor for the query exists -> if exist filter out ids 
        if customer_info.agent_ids_seen:
            database_query = await vector_db.retrieve_filter_ids(
                embeddings=embedded_query,
                limit=limit,
                collection_type=CollectionType.AGENT,
                excluded_ids=agent_ids_seen
            )
        else:
            database_query = await vector_db.retrieve(
                embeddings=embedded_query,
                limit=limit,
                collection_type=CollectionType.AGENT
            )

        #check if queried returned anything
        if not database_query.points:
            return AgentReturnedList(
                response='No results for the search.',
                returned_agents=None,
                agent_seen_lst=customer_info.agent_ids_seen
            )

        payload_lst = [point.payload for point in database_query.points if point.payload]
        #appending list of seen ids 
        agent_ids_seen = update_agent_ids_lst(
            payload_lst=payload_lst,
            ids_lst=agent_ids_seen
        )

        #returning the 
        agents_returned_lst = retrieve_queryied_agents(
            payload_lst=payload_lst
        )

        return AgentReturnedList(
            returned_agents=agents_returned_lst,
            agent_seen_lst=agent_ids_seen
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Database Error. Search failed, please try again.'
        )

"""Route to get information about specific agent"""
@customer_search_agent.get('agents/{agent_id_str}')
async def get_searched_agent(agent_id_str:str,
                             session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
                             ):
    #casting agent id to UUID
    try:
        agent_id = UUID(agent_id_str)
    except Exception:
        raise HTTPException(
            status_code='Invalid id form. Please try selecting agent again.'
        ) 

    #relational database query
    try:
        #agent query
        agent_query = await session_db.execute(select(Agent).where(
            Agent.id == agent_id
        ))
        agent = agent_query.scalar_one_or_none() #returns first agent found

        #merchant query 
        merchant_query = await session_db.execute(select(Merchant).where(
            Merchant.id == agent.merchant_id
        ))
        merchant = merchant_query.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Database error. Unable to locate agent. Please try again.'
        )

    #check if agent was successfuly queried 
    if (not agent) or (not merchant):
        raise HTTPException(
            status_code=400,
            detail='Database error. Please try selecting the agent again.'
        )

    #getting the agent's rating 
    try:
        agent_rating = await get_agents_rating(session_db)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Database error. Please try selecting the agent again.'
        )

    #agent info object 
    agent_info = AgentInfo(
        agent_id=str(agent.id),
        agent_imgicon_key=agent.imgicon_storage_key,
        agent_name=agent.name,
        agent_rating=agent_rating, 
        agent_price=(agent.agent_price_per_job / 100), #agent price stored as int -> returned as decimal
        agent_description=agent.description,
        agent_skills=agent.agent_skills
    )

    #merchant info object
    agent_mechant_info = AgentMerchantInfo(
        merchant_id=str(merchant.id),
        merchant_name=merchant.username,
        merchant_imgicon_key=merchant.merchant_imgicon_key
    )

    #returning info to the client 
    return AgentResponse(
        returned_info={
            'agent':agent_info,
            'merchant':agent_mechant_info
        }
    )