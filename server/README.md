# Pine customer server

## Overview

The customer backend is a FastAPI application exposed as `server.app:app`. `app.py` imports each route module and mounts the shared routers. `lifespan.py` creates the Postgres, Redis, and Qdrant clients, the HTTP client, event queues, Google OAuth settings, and Pine agent, then closes the shared connections at shutdown. Runtime configuration comes from `server/.env` and the Google OAuth client secret file; keep both out of source control.

Customer route handlers are under `applications/customers/routes/`. Shared database, cache, event, and agent work lives in `config/`, `services/`, and `applications/customers/agent/`. SQLAlchemy tables are in `models/` and request/response schemas are in `applications/customers/schemas/`.

The customer mobile app and route-by-route contract are documented in [`../client/mobile/README.md`](../client/mobile/README.md). The Expo Router app uses the server routes described there.

## Docker and Cloud Run

Build the image from the repository root so Docker can copy the `server/` package:

```bash
docker build -f docker/Dockerfile -t pine-server .
```

The container starts `uvicorn server.app:app` on `0.0.0.0:$PORT` (default `8080`), as required by Cloud Run. It runs as an unprivileged user with one Uvicorn worker. Provide runtime configuration through Cloud Run environment variables and Secret Manager; do not bake `server/.env`, credentials, or `client_secret.json` into the image. The Gmail OAuth routes use `GOOGLE_CLIENT_SECRET_FILE`, which defaults to `client_secret.json` for local development. In Cloud Run, mount the Secret Manager file at a separate path such as `/secrets/google/client_secret.json` and set `GOOGLE_CLIENT_SECRET_FILE` to that path. Store `STRIPE_API_KEY` and `STRIPE_WEBHOOK_SECRET` in Secret Manager, and set `PINE_CLIENT_ORIGINS` to the exact web-client origin(s).

`POSTGRES_URI` must use SQLAlchemy's async PostgreSQL driver form, such as `postgresql+asyncpg://...`; `asyncpg` is installed in the image. Make sure the Cloud Run service can reach Postgres, Redis, and Qdrant. Since job and notification SSE events use process-local queues, start with a single Cloud Run instance for reliable event delivery until those queues move to a shared broker.

## Local browser client CORS

The API enables CORS for the local Expo web preview origins `http://localhost:8081` and `http://127.0.0.1:8081`. Set `PINE_CLIENT_ORIGINS` in `server/.env` to a comma-separated allowlist of the browser client origins when the client is opened from a different host, such as a Codespaces forwarded-port URL. Include only the origin (scheme, host, and port), with no path. Native React Native requests do not use browser CORS, but the Expo web preview does. The allowlist permits the API methods and `Authorization`, `Content-Type`, and `Accept` headers used by the customer client.

## Customer flows

### Landing-page registration

The public customer and merchant landing forms both collect first name, last name, email, and phone. `POST /landing/register/customer` stores a customer lead in `CustomerRegisterModel`; `POST /landing/register/merchant` stores a merchant lead in `MerchantRegistrationModel`. These routes use separate schemas and tables. They do not create authenticated application accounts. Customer account signup for the mobile app remains under `/auth/customer/signup` and requires SMS verification.

### Authentication

1. `POST /auth/customer/signup` checks for an existing email or phone number, creates a pending SMS verification record, and returns a temporary verification token.
2. `POST /auth/customer/login` finds the account by email and phone number, creates a pending SMS verification, and returns a temporary verification token.
3. `POST /auth/customer/verify/{customer_token}` verifies the hashed code, creates the customer on signup, and stores a hashed session token. `PATCH /auth/customer/verify/update/{customer_token}` resends a code for a pending verification.
4. REST routes authenticate the bearer token in `get_current_customer`. GraphQL routes use `get_customer_context`, which validates the same session and reads optional pagination values from the GraphQL request.
5. `POST /auth/customer/logout` authenticates the current customer, deletes that device's session row, and revokes its token. Other active sessions for the customer remain valid.

### Agent discovery and chat

Search routes return active agents, their descriptions, pricing, and customer rating data. Hiring creates a customer-specific `HiredAgent` row with the agent name and ID, abilities, restrictions, current state, and price. The row ID identifies this customer’s hire and is used in the chat path: `POST /customer/home/chat/{hired_agent_id_str}`.

Chat loads separate router and tooling histories from Redis. The router classifies a message as a conversation, job creation, informative, support, or harmful request. The tooling agent receives the prior conversation and customer/hire IDs, then uses its registered tools. Conversation requests are signed and sent to the hired agent’s URL. Job requests are signed and sent to Pine’s client webhook so the offer can be queued for payment.

### Job offer and payment

1. `POST /customer/webhooks/client` verifies the agent signature, checks the customer/hired-agent queue and active-job state, assigns a unique `offer_id`, and caches the offer. If the agent is free and the queue was empty, it publishes an SSE event; otherwise it leaves the offer queued.
2. `GET /customer/webhooks/client/event` streams the authenticated customer’s offer, including the offer ID, hired-agent ID/name, description, and price.
3. `GET /customer/home/cards` returns saved cards. `POST /customer/home/payment/{payment_id_str}/{agent_id_str}/{offer_id_str}` validates the selected saved card and exact queued offer, creates/reuses a PaymentIntent keyed to the offer, and confirms it while the customer is present. If the bank requires authentication, the response includes `status: "requires_action"` and the PaymentIntent client secret; the mobile app completes that step with Stripe's native SDK, then calls `POST /customer/home/payment/confirm/{payment_intent_id}`. A succeeded PaymentIntent creates the job and payment rows in one Postgres transaction, removes the exact Redis offer, sends the signed agent request, and creates customer/merchant notifications.
4. The hired agent completes the job through `PATCH /customer/webhooks/jobs`. Pine records completion, creates notifications, and publishes the next queued offer when available. Agent-created customer requests arrive through `POST /customer/webhooks/requests`; customer answers are sent to the agent from the activity REST route.

`POST /stripe/webhook` verifies Stripe's `Stripe-Signature` header and reconciles `payment_intent.succeeded` events. It retries finalization when Pine cannot deliver the paid job. Set `STRIPE_WEBHOOK_SECRET` from the webhook endpoint created in Stripe. The payment models also store the offer ID, Stripe PaymentIntent ID, and dispatch timestamp so retries can resume without relying on the Redis processed-offer marker.

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
- Before deploying the updated Stripe flow, run [`migrations/2026-10-01-stripe-job-payment-recovery.sql`](migrations/2026-10-01-stripe-job-payment-recovery.sql) against Postgres. It adds and backfills the Stripe customer ID and adds durable offer/payment identifiers. The app does not execute this SQL automatically.
- `PATCH /customer/notifications/clear` expects the notification IDs in the currently displayed batch, with at most 50 IDs per request.

## Operational caveats

- No live service or automated test run was performed during this review. Startup and external flows still depend on valid `.env` values, reachable services, Stripe/Twilio/OpenAI credentials, and Google OAuth client configuration.
- Event queues are process-local. Multiple workers or server instances do not share SSE event signals; use a shared broker before running multiple workers.
- Job completion is committed before its notification and next-offer events are published. A later failure can leave the database updated while an event is missing; a durable outbox or reconciliation path is needed for reliable recovery.
- GraphQL pagination uses timestamps as cursors. Rows sharing the same timestamp can be skipped across pages; a compound timestamp/ID cursor would remove that edge case if the client contract is later expanded.
- The job and payment rows are committed atomically, and Stripe webhooks can retry dispatch. The remote agent request and Pine's database still cannot share a transaction; the request includes the stable job ID as an idempotency key so an agent endpoint can deduplicate retries.
- Stripe Tax is not enabled in this code. Do not collect tax until customer location, the service tax classification, the liable entity, and active tax registrations are confirmed.
