# Pine customer server

## Overview

The customer backend is a FastAPI application exposed as `server.app:app`. `app.py` imports each route module and mounts the shared routers. `lifespan.py` creates the Postgres, Redis, and Qdrant clients, the HTTP client, event queues, Google OAuth settings, and Pine agent, then closes the shared connections at shutdown. Runtime configuration comes from `server/.env` and the Google OAuth client secret file; keep both out of source control.

Customer route handlers are under `applications/customers/routes/`. Shared database, cache, event, and agent work lives in `config/`, `services/`, and `applications/customers/agent/`. SQLAlchemy tables are in `models/` and request/response schemas are in `applications/customers/schemas/`.

The customer mobile route-by-route contract is documented in [`../client/mobile/README.md`](../client/mobile/README.md). That directory contains integration documentation, not the React Native app source.

## Customer flows

### Authentication

1. `POST /auth/customer/signup` checks for an existing email or phone number, creates a pending SMS verification record, and returns a temporary verification token.
2. `POST /auth/customer/login` finds the account by email and phone number, creates a pending SMS verification, and returns a temporary verification token.
3. `POST /auth/customer/verify/{customer_token}` verifies the hashed code, creates the customer on signup, and stores a hashed session token. `PATCH /auth/customer/verify/update/{customer_token}` resends a code for a pending verification.
4. REST routes authenticate the bearer token in `get_current_customer`. GraphQL routes use `get_customer_context`, which validates the same session and reads optional pagination values from the GraphQL request.

### Agent discovery and chat

Search routes return active agents, their descriptions, pricing, and customer rating data. Hiring creates a customer-specific `HiredAgent` row with the agent name and ID, abilities, restrictions, current state, and price. The row ID identifies this customer’s hire and is used in the chat path: `POST /customer/home/chat/{hired_agent_id_str}`.

Chat loads separate router and tooling histories from Redis. The router classifies a message as a conversation, job creation, informative, support, or harmful request. The tooling agent receives the prior conversation and customer/hire IDs, then uses its registered tools. Conversation requests are signed and sent to the hired agent’s URL. Job requests are signed and sent to Pine’s client webhook so the offer can be queued for payment.

### Job offer and payment

1. `POST /customer/webhooks/client` verifies the agent signature, checks the customer/hired-agent queue and active-job state, assigns a unique `offer_id`, and caches the offer. If the agent is free and the queue was empty, it publishes an SSE event; otherwise it leaves the offer queued.
2. `GET /customer/webhooks/client/event` streams the authenticated customer’s offer, including the offer ID, hired-agent ID/name, description, and price.
3. `GET /customer/home/cards` returns saved cards. `POST /customer/home/payment/{payment_id_str}/{agent_id_str}/{offer_id_str}` validates the selected saved card and exact queued offer, charges through Stripe with a stable idempotency key, creates the job and payment records, removes that exact offer from Redis, and creates customer/merchant notifications.
4. The hired agent completes the job through `PATCH /customer/webhooks/jobs`. Pine records completion, creates notifications, and publishes the next queued offer when available. Agent-created customer requests arrive through `POST /customer/webhooks/requests`; customer answers are sent to the agent from the activity REST route.

### Activity and notifications

The activity GraphQL endpoint is `/customer/activity`; it returns pending requests, active jobs, completed jobs, and payments. Page sizes are capped at 50. REST routes under `/customer/activity` return one request/job and send customer answers or ratings.

The notification GraphQL endpoint is `/customer/notifications` and returns unread notifications in newest-first pages. `GET /customer/notifications/{notification_id_str}` loads one customer-owned notification and marks it read. `PATCH /customer/notifications/clear` accepts `{"notification_ids": ["<uuid>", ...]}` and marks only those customer-owned unread notifications as read. `GET /customer/notifications/events` streams notification events.

### Profile and email integrations

`GET /profile/page` returns customer details, the last-used saved card, active hire count, and completed-job count. `/profile/agents/{hired_agent_id}` returns one customer-owned hire with state, rating, image key, abilities, restrictions, hire time, and price. Profile GraphQL endpoints return active/fired hires and connected email integrations. `POST /profile/integrations/email/delete/{integration_id}` permanently removes an owned integration.

`POST /profile/oauth2/email/gmail` starts Google OAuth and returns the authorization URL for the client to open. Google calls `/profile/oauth2/email/gmail/redirect`; the callback verifies the HMAC-signed customer ID, exchanges the code, fetches the Gmail account address, stores the token and integration, then redirects to a success or already-connected response route. The agent tool `check_customer_gmail_email` only verifies that the requested address is connected to that customer; it does not yet read or send Gmail messages.

## Important implementation notes

- Customer and merchant webhook requests are authenticated with HMAC signatures. Merchant job/request callbacks also verify that the authenticated merchant owns the job.
- Pending offers are stored in Redis lists keyed by customer and hired-agent IDs. The SSE events and notification events use per-customer `asyncio.Queue` and `Event` objects in server memory.
- The `GmailIntegration` table has a unique integrated email. Email integrations and hired-agent abilities are represented in the SQLAlchemy models; this repository does not include a migration framework or create/update deployed tables automatically.
- `PATCH /customer/notifications/clear` expects the notification IDs in the currently displayed batch, with at most 50 IDs per request.

## Operational caveats

- No live service or automated test run was performed during this review. Startup and external flows still depend on valid `.env` values, reachable services, Stripe/Twilio/OpenAI credentials, and Google OAuth client configuration.
- Event queues are process-local. Multiple workers or server instances do not share SSE event signals; use a shared broker before running multiple workers.
- Job completion is committed before its notification and next-offer events are published. A later failure can leave the database updated while an event is missing; a durable outbox or reconciliation path is needed for reliable recovery.
- GraphQL pagination uses timestamps as cursors. Rows sharing the same timestamp can be skipped across pages; a compound timestamp/ID cursor would remove that edge case if the client contract is later expanded.
- Stripe payment, database persistence, and webhook delivery are separate operations. Stripe idempotency prevents repeating the same charge request, but the overall flow is not one atomic transaction.
