# File for building the agent's tools.
from aiohttp import ClientError, ClientSession
from agents.decorators import tool
from sqlalchemy import and_, func, select

from server.applications.customers.agent.tools.tools_schemas import (
    AgentConversation,
    AgentInfo,
    AgentJob,
    AgentRequest,
    CustomerEmailInfo,
    DataForRequest,
    HiredAgentInfo,
    HiredAgentResponse,
    RequestResponse,
    ReturnAgentURL,
)
from server.config.database import RelationalDatabase
from server.models.agents.agent import Agent, AgentState
from server.models.agents.hired_agent import HiredAgent
from server.models.integrations.email.gmail_integration import GmailIntegration
import hashlib
import hmac


"""Return the functions that the tooling agent can call."""
def retrieve_agents_tools(
    relational_db: RelationalDatabase,
    http_client: ClientSession,
    pine_server_key: str,
    client_webhook_url: str,
):
    # Find the customer's active hire and the information needed for its flow.
    @tool
    async def get_customer_hired_agent(hired_agent_info: HiredAgentInfo) -> str:
        """Verify the active hire belongs to this customer and return its IDs, name, and job price."""
        try:
            async with relational_db.async_session() as session:
                hired_agent_query = await session.execute(select(HiredAgent).where(and_(
                    HiredAgent.id == hired_agent_info.hired_agent_id,
                    HiredAgent.customer_id == hired_agent_info.customer_id,
                    HiredAgent.agent_state == AgentState.ACTIVE,
                )))
                hired_agent = hired_agent_query.scalar_one_or_none()
        except Exception:
            return 'Unable to verify this hired agent because the database query failed.'

        if not hired_agent:
            return 'No active hired agent was found for this customer.'

        return HiredAgentResponse(
            hired_agent_id=hired_agent.id,
            agent_id=hired_agent.agent_id,
            agent_name=hired_agent.name,
            job_price=hired_agent.price_per_job,
            agent_restrictions=hired_agent.agent_restrictions,
        ).model_dump_json()

    # Check whether the requested email address belongs to this customer's Gmail integrations.
    @tool
    async def check_customer_gmail_email(email_info: CustomerEmailInfo) -> bool:
        """Return whether this email address is connected to the supplied customer account."""
        try:
            async with relational_db.async_session() as session:
                customer_gmail_query = await session.execute(
                    select(GmailIntegration.id).where(and_(
                        GmailIntegration.customer_id == email_info.customer_id,
                        func.lower(GmailIntegration.integrated_email)
                        == str(email_info.email_name).lower()
                    ))
                )
                customer_gmail_id = customer_gmail_query.scalar_one_or_none()
        except Exception:
            # A failed lookup must not be treated as a verified integration.
            return False

        return customer_gmail_id is not None

    # Resolve the public agent ID to the agent's configured webhook URL.
    @tool
    async def get_hired_agent_url(agent_info: AgentInfo) -> str:
        """Return the active agent's conversation webhook URL for its public agent ID."""
        try:
            async with relational_db.async_session() as session:
                agent_query = await session.execute(select(Agent).where(and_(
                    Agent.id == agent_info.agent_id,
                    Agent.agent_state == AgentState.ACTIVE,
                )))
                agent = agent_query.scalar_one_or_none()
        except Exception:
            return 'Unable to retrieve the agent URL because the database query failed.'

        if not agent:
            return 'No active agent was found for this agent ID.'

        return ReturnAgentURL(agent_url=agent.agents_webhook_url).model_dump_json()

    # Sign the exact JSON body that will be sent to the next endpoint.
    @tool
    def pine_request_data(agent_data: AgentJob | AgentConversation) -> str:
        """Sign either a job offer for the client webhook or a conversation request for the agent."""
        try:
            pine_signature = hmac.new(
                key=pine_server_key.encode('utf-8'),
                msg=agent_data.model_dump_json().encode('utf-8'),
                digestmod=hashlib.sha256,
            ).hexdigest()
        except Exception:
            return 'Unable to create the request signature.'

        return AgentRequest(
            pine_signature=pine_signature,
            agent_job=agent_data if isinstance(agent_data, AgentJob) else None,
            conversation_data=agent_data if isinstance(agent_data, AgentConversation) else None,
        ).model_dump_json()

    # A task request first goes to Pine's client webhook to create an offer.
    @tool
    def create_agent_job_request(agent_request: AgentRequest) -> str:
        """Build the signed request to Pine's client webhook, which creates the customer's offer."""
        if agent_request.agent_job is None or agent_request.conversation_data is not None:
            return 'A signed job payload is required to create a job offer.'

        request_header = {
            'Content-Type': 'application/json',
            'Signature': agent_request.pine_signature,
        }
        return DataForRequest(
            request_url=client_webhook_url,
            headers=request_header,
            data=agent_request.agent_job.model_dump_json(),
        ).model_dump_json()

    # A conversation request goes directly to the selected hired agent.
    @tool
    def create_agent_conversation_request(agent_url: str, agent_request: AgentRequest) -> str:
        """Build the signed conversation request to the hired agent's own webhook URL."""
        if agent_request.conversation_data is None or agent_request.agent_job is not None:
            return 'A signed conversation payload is required to contact the agent.'

        request_header = {
            'Content-Type': 'application/json',
            'Signature': agent_request.pine_signature,
        }
        return DataForRequest(
            request_url=agent_url,
            headers=request_header,
            data=agent_request.conversation_data.model_dump_json(),
        ).model_dump_json()

    # Send a prepared request and return both its HTTP status and response body.
    @tool
    async def send_agent_request(agent_request_data: DataForRequest) -> str:
        """POST a signed request and report whether the endpoint accepted it."""
        try:
            async with http_client.post(
                url=agent_request_data.request_url,
                headers=agent_request_data.headers,
                data=agent_request_data.data,
            ) as url_response:
                response_text = await url_response.text()
                return RequestResponse(
                    accepted=200 <= url_response.status < 300,
                    status_code=url_response.status,
                    response=response_text,
                ).model_dump_json()
        except ClientError:
            return RequestResponse(
                accepted=False,
                status_code=None,
                response='Unable to reach the request destination.',
            ).model_dump_json()
        except Exception:
            return RequestResponse(
                accepted=False,
                status_code=None,
                response='The request could not be completed.',
            ).model_dump_json()

    # Return the decorated functions for the tooling agent configuration.
    return [
        get_customer_hired_agent,
        check_customer_gmail_email,
        get_hired_agent_url,
        pine_request_data,
        create_agent_job_request,
        create_agent_conversation_request,
        send_agent_request,
    ]
