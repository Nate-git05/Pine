#File for the service functions for the customer profile page
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from strawberry import Info

from server.applications.customers.schemas.pages.profile_schemas import (
    CustomerHiredAgent,
    CustomerHiredAgentsResponse,
    HiredAgentState
)
from server.models.agents.agent import AgentState
from server.models.agents.hired_agent import HiredAgent
from server.models.activities.jobs.agent_job import AgentJob, AgentJobState
from server.models.users.customers import Customer


"""Get the customer's hired agents and each agent's average customer job rating."""
async def get_customer_hired_agents(
    session_db: AsyncSession,
    customer_id: UUID,
    agent_state: AgentState
) -> list[tuple[HiredAgent, float]]:
    # Query the customer's hired agents for the requested state.
    hired_agents_query = await session_db.execute(
        select(HiredAgent)
        .where(and_(
            HiredAgent.customer_id == customer_id,
            HiredAgent.agent_state == agent_state
        ))
        .order_by(HiredAgent.name)
    )
    hired_agents = hired_agents_query.scalars().all()

    if not hired_agents:
        return []

    hired_agent_ids = [hired_agent.id for hired_agent in hired_agents]

    # Average only ratings from this customer's completed jobs for each hired agent.
    job_ratings_query = await session_db.execute(
        select(
            AgentJob.hired_agent_id,
            func.avg(AgentJob.job_rating)
        )
        .where(and_(
            AgentJob.customer_id == customer_id,
            AgentJob.hired_agent_id.in_(hired_agent_ids),
            AgentJob.job_state == AgentJobState.DONE,
            AgentJob.job_rating.is_not(None)
        ))
        .group_by(AgentJob.hired_agent_id)
    )
    customer_job_ratings = {
        hired_agent_id: float(average_rating)
        for hired_agent_id, average_rating in job_ratings_query.all()
    }

    return [
        (hired_agent, customer_job_ratings.get(hired_agent.id, 0.0))
        for hired_agent in hired_agents
    ]


"""Get one hired agent and its average rating from this customer's completed jobs."""
async def get_customer_hired_agent(
    session_db: AsyncSession,
    customer_id: UUID,
    hired_agent_id: UUID
) -> tuple[HiredAgent, float] | None:
    # Find this hired-agent row only if it belongs to the authenticated customer.
    hired_agent_query = await session_db.execute(
        select(HiredAgent).where(and_(
            HiredAgent.id == hired_agent_id,
            HiredAgent.customer_id == customer_id
        ))
    )
    hired_agent = hired_agent_query.scalar_one_or_none()

    if not hired_agent:
        return None

    # Calculate the rating from this customer's completed jobs for this hired agent.
    job_rating_query = await session_db.execute(
        select(func.avg(AgentJob.job_rating)).where(and_(
            AgentJob.customer_id == customer_id,
            AgentJob.hired_agent_id == hired_agent.id,
            AgentJob.job_state == AgentJobState.DONE,
            AgentJob.job_rating.is_not(None)
        ))
    )
    average_rating = job_rating_query.scalar_one_or_none()

    return hired_agent, float(average_rating) if average_rating is not None else 0.0


"""Build the response for one of the customer's hired-agent lists."""
async def _get_customer_agents(
    customer_context: Info,
    agent_state: AgentState
) -> CustomerHiredAgentsResponse:
    #getting the validated customer and database session from the shared context
    customer: Customer | None = customer_context.context.get('customer')
    session_db: AsyncSession | None = customer_context.context.get('database_session')

    if not customer or not session_db:
        return CustomerHiredAgentsResponse(
            status_code=400,
            response='Unable to load your agents.',
            hired_agents=None
        )

    #querying the customer's hired agents and their ratings from customer jobs
    try:
        customer_agents = await get_customer_hired_agents(
            session_db=session_db,
            customer_id=customer.id,
            agent_state=agent_state
        )
    except Exception:
        return CustomerHiredAgentsResponse(
            status_code=500,
            response='Unable to load your agents. Please try again.',
            hired_agents=None
        )

    if not customer_agents:
        return CustomerHiredAgentsResponse(
            status_code=200,
            response='No agents were found for this status.',
            hired_agents=[]
        )

    #building the returned hired-agent list
    agents_returned = [
        CustomerHiredAgent(
            id=str(hired_agent.id),
            name=hired_agent.name,
            description=hired_agent.description,
            state=HiredAgentState(hired_agent.agent_state),
            rating=job_rating
        )
        for hired_agent, job_rating in customer_agents
    ]

    return CustomerHiredAgentsResponse(
        status_code=200,
        response=None,
        hired_agents=agents_returned
    )
