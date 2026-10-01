"""GraphQL query for the customer's connected email integrations."""
import strawberry
from strawberry import Info, Schema
from strawberry.fastapi import GraphQLRouter
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from server.applications.customers.services.auth.auth_service import get_customer_context
from server.models.users.customers import Customer
from server.models.integrations.email.gmail_integration import GmailIntegration


@strawberry.type
class CustomerEmailIntegration:
    id: str
    integration_type: str
    integrated_email: str
    integrated_at: datetime


@strawberry.type
class CustomerEmailIntegrationsResponse:
    status_code: int
    response: str | None
    integrations: list[CustomerEmailIntegration] | None


"""Query object for the profile page's connected email list."""
@strawberry.type
class CustomerEmailIntegrationsQuery:
    @strawberry.field
    async def customer_email_integrations(
        self,
        customer_info: Info
    ) -> CustomerEmailIntegrationsResponse:
        # Retrieve the authenticated customer and database session from the shared context.
        customer: Customer | None = customer_info.context.get('customer')
        session_db: AsyncSession | None = customer_info.context.get('database_session')

        if not customer or not session_db:
            return CustomerEmailIntegrationsResponse(
                status_code=400,
                response='Unable to load your email integrations.',
                integrations=None
            )

        # Return every connected email account as one newest-first list.
        try:
            integrations_query = await session_db.execute(
                select(GmailIntegration)
                .where(GmailIntegration.customer_id == customer.id)
                .order_by(desc(GmailIntegration.integrated_at))
            )
            customer_integrations = integrations_query.scalars().all()
        except Exception:
            return CustomerEmailIntegrationsResponse(
                status_code=500,
                response='Unable to load your email integrations.',
                integrations=None
            )

        if not customer_integrations:
            return CustomerEmailIntegrationsResponse(
                status_code=200,
                response='No email accounts are connected.',
                integrations=[]
            )

        integrations_returned = [
            CustomerEmailIntegration(
                id=str(integration.id),
                integration_type=str(integration.integration_type),
                integrated_email=str(integration.integrated_email),
                integrated_at=integration.integrated_at
            )
            for integration in customer_integrations
        ]

        return CustomerEmailIntegrationsResponse(
            status_code=200,
            response=None,
            integrations=integrations_returned
        )


# Mount this query separately from the other profile GraphQL operations.
customer_email_integrations_schema = Schema(query=CustomerEmailIntegrationsQuery)
customer_email_integrations_router = GraphQLRouter(
    schema=customer_email_integrations_schema,
    path='/customer/profile/integrations/email',
    context_getter=get_customer_context
)
