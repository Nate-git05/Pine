"""Stripe event endpoint for payment reconciliation."""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Annotated
from aiohttp import ClientSession
from sqlalchemy.ext.asyncio import AsyncSession
from stripe import SignatureVerificationError, Webhook

from server.config.apis import NotificationEvents
from server.config.database import CacheDatabase
from server.dependencies import (
    get_async_http,
    get_cache_db,
    get_notifications_events,
    get_relational_db_session,
    get_server_key,
    get_stripe_webhook_secret,
)
from server.applications.customers.services.pages.home_service import finalize_paid_job

stripe_webhook_router = APIRouter(prefix='/stripe', tags=['Stripe webhooks'])


@stripe_webhook_router.post('/webhook')
async def receive_stripe_webhook(
    request:Request,
    session_db:Annotated[AsyncSession, Depends(get_relational_db_session)],
    cache_db:Annotated[CacheDatabase, Depends(get_cache_db)],
    http_client:Annotated[ClientSession, Depends(get_async_http)],
    pine_server_key:Annotated[str, Depends(get_server_key)],
    notification_events:Annotated[NotificationEvents, Depends(get_notifications_events)],
    webhook_secret:Annotated[str | None, Depends(get_stripe_webhook_secret)],
):
    """Verify Stripe's signature and recover successful job dispatches."""
    if not webhook_secret:
        raise HTTPException(status_code=503, detail='Stripe webhook is not configured.')

    payload = await request.body()
    signature = request.headers.get('Stripe-Signature')
    if not signature:
        raise HTTPException(status_code=400, detail='Missing Stripe signature.')

    try:
        event = Webhook.construct_event(payload, signature, webhook_secret)
    except (ValueError, SignatureVerificationError) as error:
        raise HTTPException(status_code=400, detail='Invalid Stripe webhook signature.') from error

    #Other event types are acknowledged; the customer-facing setup callback persists saved cards.
    if event.type != 'payment_intent.succeeded':
        return {'received':True}

    try:
        await finalize_paid_job(
            session_db=session_db,
            cache_db=cache_db,
            http_client=http_client,
            pine_server_key=pine_server_key,
            notification_events=notification_events,
            payment_intent=event.data.object,
        )
    except Exception as error:
        #A non-2xx response lets Stripe retry dispatch after a temporary Pine failure.
        raise HTTPException(status_code=500, detail='Unable to reconcile this successful payment yet.') from error

    return {'received':True}
