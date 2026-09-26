#File for the webhook thats communicates directly to the client 
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.applications.customers.routes.webhooks.apis.job_webhook import customer_api_webhook_router
from server.app import (
    get_cache_db,
    get_server_key
)
from server.applications.customers.schemas.webhooks.webhook_schema import ClientWebhook
from server.config.database import CacheDatabase
from typing import Annotated
import hmac
import hashlib

"""Route gets requests from agent/job/integrations webhook to send job over to client"""
@customer_api_webhook_router.post('/client')
async def send_cached_job(client_signature:Annotated[str, Depends()],
                          customer_info:ClientWebhook,
                          pine_server_key:Annotated[str, Depends(get_server_key)])