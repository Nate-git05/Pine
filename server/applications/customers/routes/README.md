# Customer routes

The authoritative startup and flow guide is [`server/README.md`](../../../README.md). This page records which customer router modules participate in the running app.

## Registration

`server/app.py` imports and includes these routers. App-state dependency getters live in `server/dependencies.py`; this keeps route modules from importing getters through the app entry point.

- `routes/auth/signup.py` owns the shared `/auth/customer` router; `login.py` and `verify.py` attach their handlers to it and are imported before inclusion.
- `routes/pages/home/customer_payment.py` attaches saved-card and payment operations to the router created in `pages/home/agent_chat.py` (`/customer/home`). That module currently declares no chat endpoints.
- `routes/pages/search/agent_search.py` creates `/customer/search`; `hire_agent.py` is imported so hire/fire handlers attach to that router.
- The activity REST files each create `/customer/activity`; `activity/graphql/activity_page.py` adds GraphQL at the same prefix.
- `pages/home/notifications/notifications_sse.py` exposes `/customer/notifications/events`; the notification GraphQL and REST modules add the list, detail, and clear routes under the same prefix. The SSE router is registered before the REST `/{notification_id}` route so `/events` reaches the stream handler.
- `routes/webhooks/apis/job_webhook.py` creates `/customer/webhooks`; `client_webhook.py` and `request_webhook.py` attach more handlers before it is included.

The import side effects matter: moving/removing those imports can remove handlers from a shared router. Profile REST/GraphQL are not included. Customer/merchant landing registration and merchant auth/routes are also not mounted by this app.

## Authentication boundaries

Customer page endpoints use the customer session dependency, except public SMS auth routes and Stripe browser-return callbacks. `/customer/webhooks/client` is called by agent/merchant services and uses Pine's `Signature`; `/customer/webhooks/jobs` and `/requests` use a merchant `Api-Key` and `Signature`. The [webhook README](webhooks/apis/README.md) describes callback direction and signing.

For request paths and end-to-end behavior, use the [server guide](../../../README.md). Do not infer route availability from an existing directory or schema.
