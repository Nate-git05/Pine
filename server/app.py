# File for starting up the application for the server.
from fastapi import FastAPI

from server.lifespan import lifespan
from server.applications.customers.routes.auth.signup import customer_auth_router
from server.applications.customers.routes.auth import login as _customer_login_routes
from server.applications.customers.routes.auth import verify as _customer_verify_routes
from server.applications.customers.routes.pages.home.customer_payment import customer_home_router
from server.applications.customers.routes.pages.search.agent_search import customer_search_router
from server.applications.customers.routes.pages.search import hire_agent as _customer_hire_routes
from server.applications.customers.routes.pages.activity.rest.customer_jobs import (
    customer_activity_router as customer_jobs_router,
)
from server.applications.customers.routes.pages.activity.rest.customer_requests import (
    customer_activity_router as customer_requests_router,
)
from server.applications.customers.routes.pages.home.notifications.notifications_sse import (
    customer_sse_router,
)
from server.applications.customers.routes.pages.home.notifications.graphql.notifications_page import (
    notifications_page_router,
)
from server.applications.customers.routes.pages.home.notifications.rest.notification_routes import (
    customer_notification_router,
)
from server.applications.customers.routes.webhooks.apis.job_webhook import customer_api_webhook_router
from server.applications.customers.routes.webhooks.apis import client_webhook as _client_webhook_routes
from server.applications.customers.routes.webhooks.apis import request_webhook as _request_webhook_routes
from server.applications.customers.routes.pages.activity.graphql.activity_page import (
    activity_page_graphql_router,
)


# Initialize the app after importing modules that attach routes to shared routers.
app = FastAPI(lifespan=lifespan)

for router in (
    customer_auth_router,
    customer_home_router,
    customer_search_router,
    customer_jobs_router,
    customer_requests_router,
    customer_sse_router,
    notifications_page_router,
    customer_notification_router,
    customer_api_webhook_router,
    activity_page_graphql_router,
):
    app.include_router(router)
