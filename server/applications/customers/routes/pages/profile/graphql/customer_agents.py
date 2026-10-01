#File for the GraphQL routes for the customer profile's agents
import strawberry
from strawberry import (
    Info,
    Schema
)
from strawberry.fastapi import GraphQLRouter

from server.applications.customers.services.auth.auth_service import get_customer_context
from server.applications.customers.schemas.pages.profile_schemas import (
    CustomerHiredAgentsResponse
)
from server.applications.customers.services.pages.profile_service import (
    _get_customer_agents
)
from server.models.agents.agent import AgentState


"""Query object for the customer profile's active and fired agents."""
@strawberry.type
class CustomerAgentsQuery:
    #query for the customer's active hired agents
    @strawberry.field
    async def active_hired_agents(
        self,
        customer_context: Info
    ) -> CustomerHiredAgentsResponse:
        return await _get_customer_agents(
            customer_context=customer_context,
            agent_state=AgentState.ACTIVE
        )

    #query for the customer's fired hired agents
    @strawberry.field
    async def fired_hired_agents(
        self,
        customer_context: Info
    ) -> CustomerHiredAgentsResponse:
        return await _get_customer_agents(
            customer_context=customer_context,
            agent_state=AgentState.FIRED
        )


customer_agents_schema = Schema(query=CustomerAgentsQuery)
customer_agents_graphql_router = GraphQLRouter(
    schema=customer_agents_schema,
    path='/customer/profile/agents',
    context_getter=get_customer_context
)
