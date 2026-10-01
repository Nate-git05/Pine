"""REST route for removing one of the customer's connected email accounts."""
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.applications.customers.routes.pages.profile.rest.customer_profile import (
    customer_profile_router,
)
from server.applications.customers.schemas.pages.profile_schemas import (
    EmailIntegrationDeleteResponse,
)
from server.applications.customers.services.auth.auth_service import get_current_customer
from server.dependencies import get_relational_db_session
from server.models.integrations.email.gmail_integration import GmailIntegration
from server.models.users.customers import Customer


"""Route for a customer to remove a connected email account."""
@customer_profile_router.post('/integrations/email/delete/{integration_id}')
async def delete_customer_email_integration(
    integration_id: UUID,
    customer: Annotated[Customer, Depends(get_current_customer)],
    session_db: Annotated[AsyncSession, Depends(get_relational_db_session)]
) -> EmailIntegrationDeleteResponse:
    # Find the integration under this customer so another customer's row cannot be deleted.
    try:
        integration_query = await session_db.execute(
            select(GmailIntegration).where(and_(
                GmailIntegration.id == integration_id,
                GmailIntegration.customer_id == customer.id
            ))
        )
        customer_integration = integration_query.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail='Unable to look up this email integration. Please try again.'
        )

    if not customer_integration:
        raise HTTPException(
            status_code=404,
            detail='Unable to find this email integration for your account.'
        )

    # Remove the integration and its stored OAuth tokens permanently.
    try:
        await session_db.delete(customer_integration)
        await session_db.commit()
    except Exception:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail='Unable to remove this email integration. Please try again.'
        )

    return EmailIntegrationDeleteResponse(
        response='Email integration was successfully removed.'
    )
