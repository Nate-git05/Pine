# File for the OAuth2 integration for customer Gmail.
import asyncio
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

import google_auth_oauthlib.flow
from fastapi import Depends, Query, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from googleapiclient.discovery import build
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.applications.customers.routes.pages.profile.rest.customer_profile import customer_profile_router
from server.applications.customers.schemas.pages.profile_schemas import (
    EmailIntegrationType,
    GmailIntegrationResponse,
    GoogleRedirectURL,
)
from server.applications.customers.services.auth.auth_service import get_current_customer
from server.config.configuration import GOOGLE_CLIENT_SECRET_FILE
from server.dependencies import (
    get_google_oauth_info,
    get_relational_db_session,
    get_server_key,
)
from server.models.integrations.email.gmail_integration import GmailIntegration
from server.models.users.customers import Customer


"""Route for a customer to start connecting their Gmail account."""
@customer_profile_router.post('/oauth2/email/gmail', response_model=GoogleRedirectURL)
def customer_integrate_email(
    customer: Annotated[Customer, Depends(get_current_customer)],
    google_api_info: Annotated[dict, Depends(get_google_oauth_info)],
    pine_server_key: Annotated[str, Depends(get_server_key)],
):
    # Configure Google's OAuth flow and the callback registered for this app.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRET_FILE,
        scopes=google_api_info.get('google_scopes'),
    )
    flow.redirect_uri = google_api_info.get('redirect_url')

    # Sign the customer ID so the callback can identify the customer without
    # relying on the WebView to preserve the app's authorization header.
    signature = hmac.new(
        key=pine_server_key.encode('utf-8'),
        msg=customer.id.bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()
    google_state = f'{customer.id}-{signature}'

    authorization_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        state=google_state,
    )

    return GoogleRedirectURL(redirect_url=authorization_url)


"""Redirect URL Google calls after the customer authorizes Gmail."""
@customer_profile_router.get('/oauth2/email/gmail/redirect')
async def gmail_redirect(
    request: Request,
    session_db: Annotated[AsyncSession, Depends(get_relational_db_session)],
    pine_server_key: Annotated[str, Depends(get_server_key)],
    google_api_info: Annotated[dict, Depends(get_google_oauth_info)],
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
):
    # Google sends an error query parameter when the customer denies access.
    if error:
        raise HTTPException(status_code=400, detail='Google Gmail authorization was not completed.')
    if not code or not state:
        raise HTTPException(status_code=400, detail='The Google OAuth response is incomplete.')

    # UUIDs contain hyphens, so split at the final separator before the HMAC.
    try:
        customer_id_str, signature = state.rsplit('-', 1)
        customer_id = UUID(customer_id_str)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail='The OAuth state is invalid or incomplete.')

    expected_signature = hmac.new(
        key=pine_server_key.encode('utf-8'),
        msg=customer_id.bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected_signature, signature):
        raise HTTPException(status_code=400, detail='The OAuth state signature is invalid.')

    # Confirm the signed customer still exists before saving an integration.
    try:
        customer_query = await session_db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = customer_query.scalar_one_or_none()
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail='Unable to look up the customer for this Google connection.',
        ) from error
    if not customer:
        raise HTTPException(
            status_code=404,
            detail='The customer for this Google connection could not be found.',
        )

    # Exchange the authorization code and fetch the verified Google account.
    try:
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            GOOGLE_CLIENT_SECRET_FILE,
            scopes=google_api_info.get('google_scopes'),
            state=state,
        )
        flow.redirect_uri = google_api_info.get('redirect_url')
        await asyncio.to_thread(flow.fetch_token, code=code)
        credentials = flow.credentials
        gmail_service = await asyncio.to_thread(
            build,
            'gmail',
            'v1',
            credentials=credentials,
        )
        profile = await asyncio.to_thread(
            gmail_service.users().getProfile(userId='me').execute
        )
        customer_gmail = profile.get('emailAddress')
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail='Google could not complete the Gmail connection.',
        ) from error

    if not customer_gmail or not credentials.token or not credentials.refresh_token:
        raise HTTPException(
            status_code=400,
            detail='Google did not return the Gmail account and refresh token required to connect.',
        )

    # Gmail addresses are unique in this table, so check ownership before insert.
    try:
        integration_query = await session_db.execute(
            select(GmailIntegration).where(
                GmailIntegration.integrated_email == customer_gmail
            )
        )
        existing_integration = integration_query.scalar_one_or_none()
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail='Unable to check whether this Gmail account is already connected.',
        ) from error

    if existing_integration:
        if existing_integration.customer_id == customer_id:
            return RedirectResponse(
                url=str(request.url_for('return_gmail_already_exists')),
                status_code=303,
            )
        raise HTTPException(
            status_code=409,
            detail='This Gmail account is already connected to another Pine customer.',
        )

    token_exp_time = credentials.expiry
    if token_exp_time and token_exp_time.tzinfo is None:
        token_exp_time = token_exp_time.replace(tzinfo=timezone.utc)
    if not token_exp_time:
        raise HTTPException(
            status_code=502,
            detail='Google did not return an expiration time for the Gmail token.',
        )

    new_customer_integrated_gmail = GmailIntegration(
        name=customer.name,
        integrated_email=customer_gmail,
        integration_type=EmailIntegrationType.GMAIL,
        oauth2_token=credentials.token,
        refresh_token=credentials.refresh_token,
        token_exp_time=token_exp_time,
        customer_id=customer_id,
        integrated_at=datetime.now(timezone.utc),
    )

    try:
        session_db.add(new_customer_integrated_gmail)
        await session_db.commit()
    except Exception as error:
        await session_db.rollback()
        raise HTTPException(
            status_code=500,
            detail='Unable to save the Gmail connection. Please try again.',
        ) from error

    return RedirectResponse(
        url=str(request.url_for('return_success_response')),
        status_code=303,
    )


"""Route shown after Gmail connects successfully."""
@customer_profile_router.get('/oauth2/gmail/success', name='return_success_response')
def return_success_response():
    return GmailIntegrationResponse(response='Gmail is successfully connected.')


"""Route shown when this Gmail account is already connected to the customer."""
@customer_profile_router.get('/oauth2/gmail/exists', name='return_gmail_already_exists')
def return_gmail_already_exists():
    return GmailIntegrationResponse(response='Gmail is already connected.')
