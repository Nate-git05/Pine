# Pine server: end-to-end guide

This guide describes the server as it is implemented in this checkout. The application is an async FastAPI customer backend with Postgres persistence, Redis temporary state, Qdrant agent search, and integrations with Twilio, OpenAI, and Stripe. The customer mobile integration is documented separately in [`../client/mobile/README.md`](../client/mobile/README.md).

## Scope and current completeness

The mounted customer API supports SMS signup/login, agent search and hire/fire, saved-card setup, payment for an agent's proposed job, activity lists/details/actions, customer notification SSE, and merchant/agent callbacks. The conversational product is not complete server-side: there is no chat message/history API or customer hired-agent list. Profile APIs and notification history/read APIs are also not implemented. Merchant web routes, merchant auth, and landing registration routers are not registered in this FastAPI app. A directory or schema file by itself does not mean a route is available.

## Starting the application

The ASGI object is `server.app:app`. The app's lifespan initializes shared adapters and state before serving requests, then closes them on shutdown:

1. Create an async SQLAlchemy engine/session factory for Postgres.
2. Create the Redis client.
3. Create the Qdrant client and ensure the `agents` collection exists with 1024-dimensional cosine vectors.
4. Build shared Twilio/OpenAI API access and create separate in-process event managers for job offers and customer notifications.
5. Store shared dependencies (server signing key, phone number, job callback URL, Stripe key, HTTP session) on `app.state`.

Configuration is read by `server/config/configuration.py` from process environment and `server/.env`; required settings include Postgres, Redis, Qdrant, Twilio, OpenAI, Stripe, Pine signing key/phone number, embedding model, and job callback URL. Do not copy credentials into docs or logs. Startup depends on external services being reachable. The repository does not include a migration runner or deployment manifest; inspect `requirements.txt` and the environment before starting a local or deployed instance.

## Request lifecycle and shared dependencies

- `app.py` owns the FastAPI lifespan, `app.state` getters, and router registration. Route handlers use FastAPI dependencies for the database session, Redis, Qdrant, API clients, and authenticated customer.
- `RelationalDatabase.get_db()` yields one async SQLAlchemy session per request. Handlers/services generally commit their writes directly and rollback local failed writes; a complete business flow can have multiple separate commits.
- `CacheDatabase` wraps Redis key/value and list operations. Verification state, pending job offers, payment locks/results, and a completion callback queue use Redis. Default key TTLs are 600 seconds unless a route passes another value.
- `VectorDatabase` wraps the Qdrant `agents` collection. Search embeds the submitted text with the configured OpenAI model and queries payloads; Postgres then supplies full agent details.
- `APIWrapper` constructs Twilio/OpenAI clients. Stripe operations are made through the Stripe Python library in the payment code. A shared `aiohttp.ClientSession` sends outbound callbacks.
- Most REST customer routes require `Authorization: Bearer <session-token>`. Webhook callback routes instead authenticate the merchant API key and request signature. Stripe return URLs are browser callbacks and are not customer session endpoints.

## Routes actually registered

All paths are mounted without an `/api/v1` prefix. The following table reflects routers included in `app.py` and route functions attached to those router objects.

| Method | Path | Auth / caller | Purpose |
| --- | --- | --- | --- |
| `POST` | `/auth/customer/signup` | Public | Begin SMS signup |
| `POST` | `/auth/customer/login` | Public | Begin SMS login |
| `POST` | `/auth/customer/verify/{temporary_token}` | Public | Verify code and create session |
| `PATCH` | `/auth/customer/verify/update/{temporary_token}` | Public | Resend SMS code |
| `POST` | `/customer/search/agents?limit=10` | Customer Bearer | Semantic agent search |
| `GET` | `/customer/search/agents/{agent_id}` | Customer Bearer | Agent/merchant detail |
| `POST` | `/customer/search/agent/hire/{agent_id}` | Customer Bearer | Create customer-specific hire |
| `PATCH` | `/customer/search/agent/fire/{agent_hire_id}` | Customer Bearer | Mark hire as fired |
| `GET` | `/customer/home/cards` | Customer Bearer | List saved card metadata |
| `POST` | `/customer/home/payment/add` | Customer Bearer | Create Stripe card-setup Checkout session |
| `GET` | `/customer/home/payment/add/success` | Stripe browser return | Validate setup and save card |
| `GET` | `/customer/home/payment/add/failed` | Stripe browser return | Handle canceled/failed setup |
| `POST` | `/customer/home/payment/{payment_id}/{offer_id}` | Customer Bearer | Charge selected saved method and accept offer |
| `POST` | `/customer/activity` | Customer Bearer | Activity GraphQL endpoint (GraphQLRouter also supports GET queries) |
| `GET` | `/customer/activity/jobs/{job_id}` | Customer Bearer | Job details |
| `POST` | `/customer/activity/job/rating/{job_id}` | Customer Bearer | Rate completed job |
| `GET` | `/customer/activity/jobs/requests/{request_id}` | Customer Bearer | Request details |
| `POST` | `/customer/activity/request/answer/{request_id}` | Customer Bearer | Send response to agent request |
| `GET` | `/customer/notifications/events` | Customer Bearer | Customer notification SSE |
| `POST` | `/customer/webhooks/client` | Agent/merchant service using Pine `Signature` | Submit/caches a proposed job offer |
| `GET` | `/customer/webhooks/client/event` | Customer Bearer | Customer incoming-offer SSE |
| `PATCH` | `/customer/webhooks/jobs` | Merchant `Api-Key` + `Signature` | Mark job complete and notify |
| `POST` | `/customer/webhooks/requests` | Merchant `Api-Key` + `Signature` | Create customer request and notify |

The GraphQL router uses the prefix itself as its endpoint; there is no additional `/graphql` suffix. FastAPI/GraphQL introspection and docs in a running deployment are useful for confirming the installed version's exact schema and generated OpenAPI paths.

## End-to-end customer flows

### 1. Signup and session authentication

1. The client posts name, email, and phone to `/auth/customer/signup`. The handler checks for duplicate email/phone, stores a pending `SMSVerification` row, hashes the 6-digit code with bcrypt, sends it with Twilio, and stores temporary signup data in Redis.
2. Login posts email and phone to `/auth/customer/login`. If they identify an existing customer, the handler sends an SMS code and stores a temporary login state.
3. The client posts the code to `/auth/customer/verify/{temporary_token}`. Verification consumes the pending flow; signup creates the customer, while login loads the existing customer. Both create a random UUID session token and persist only an HMAC-SHA256 hash tied to the customer with a 60-day expiry.
4. Authenticated routes parse the Bearer token, hash it with the server secret, look up the session, check expiry, update `validated_at`, and load the customer. The returned session token is an opaque UUID, not a JWT. There is no mounted logout, refresh, or password reset route.

Verification temporary tokens/data use Redis's default 600-second TTL. Three incorrect code attempts trigger code regeneration and SMS resend. Errors are usually FastAPI `{"detail": "..."}` responses, but status codes are not fully uniform.

### 2. Search and hire an agent

1. The client posts search text and optional seen agent IDs to `/customer/search/agents`. The server creates an OpenAI embedding and asks Qdrant for matching `agents` payloads, filtering IDs already seen when supplied. Payloads include agent ID/name/description/price; search returns prices in dollars.
2. `/customer/search/agents/{agent_id}` loads the agent and merchant from Postgres and calculates rating from rated completed jobs.
3. `/customer/search/agent/hire/{agent_id}` stores a customer-specific `HiredAgent` row, including restrictions and copied agent display fields, and creates a merchant notification. Fire marks that hire inactive/fired.

There is no API to list a customer's hires, and hiring does not establish a chat transport. The mobile app cannot yet reload its home conversation list from the backend.

### 3. Job offer, saved card, payment, and dispatch

1. An agent/merchant service calls `POST /customer/webhooks/client` with a Pine `Signature` HMAC over the serialized offer body. The offer includes customer ID, agent ID/name, job name/description, and positive `job_price` in cents.
2. Pine generates a unique `offer_id`, stores the full offer in Redis under a customer/offer key for 900 seconds, and publishes it to `IncomingJobsEvents`. The customer's authenticated `/customer/webhooks/client/event` SSE sends the offer (display `job_price` converted to dollars). The customer UI must retain the `offer_id` from that event.
3. `/customer/home/cards` lists saved payment records using Pine payment UUIDs and retrieves card metadata from Stripe. If needed, `/customer/home/payment/add` creates Stripe Checkout in setup mode. Stripe's success callback validates the session/setup intent and stores the exact PaymentMethod; the client should then refresh the cards list.
4. The client posts `/customer/home/payment/{payment_id}/{offer_id}` with the selected Pine saved-payment ID and event offer ID. The handler acquires a short Redis lock, checks processed-offer state, validates card ownership, offer ownership, positive cents price, and an active hire for the offering agent, then creates an off-session USD Stripe PaymentIntent with a stable idempotency key.
5. After Stripe says `succeeded`, the server creates and commits an active `AgentJob`, creates/commits a `JobPayments` history record, records the processed offer result in Redis, and consumes the pending offer. It looks up the hired agent's webhook URL and sends a Pine-signed job payload. Then it writes customer and merchant notification rows and publishes a customer notification event.

The charge, job record, payment record, processed-offer key, outbound agent callback, notification rows, and SSE publish do not share one transaction or durable outbox. In particular, job and payment records are committed separately, and a callback/notification failure can happen after the customer has been charged. The route returns an error for some post-charge failures; clients must check Activity before retrying. Idempotency protects the Stripe operation for the same offer/payment method, but it does not guarantee atomic job delivery or recovery. There is no automated reconciliation worker or refund flow documented here.

### 4. Agent callbacks, activity, and notifications

- `PATCH /customer/webhooks/jobs` accepts merchant API credentials, verifies the HMAC signature, confirms the API key's merchant owns the agent associated with the job, then marks the job done and stores its summary. It writes customer/merchant notification rows and publishes the customer SSE event. It also tries to pop a Redis completion-callback list and POST any cached payload to configured `JOB_WEBHOOK_URL` with a Pine `Signature`; no code in this checkout writes to that list, so this forwarding step appears to be a no-op unless another process seeds it.
- `POST /customer/webhooks/requests` verifies merchant credentials/signature and job ownership, creates an unhandled `AgentJobRequest` plus customer notification, and publishes a customer notification event.
- Activity GraphQL lists job requests, active jobs, completed jobs, and job payments. REST gives one job/request detail, accepts ratings only for completed unrated jobs, and sends a 150-character customer response to the agent's webhook before marking the request handled.
- `/customer/notifications/events` emits live customer notifications. Notification rows are stored in Postgres, but there is no registered notification list/read API. Event SSE does not replay old events after disconnect.

## Persistence and money conventions

SQLAlchemy models are under `models/`; most IDs are UUIDs generated in Python. Important records include `Customer`, `SessionAuthentication`, `SMSVerification`, `Agent`, `HiredAgent`, `AgentJob`, `AgentJobRequest`, `JobPayments`, `StripePayment`, and `Notification`. `Customer.__tablename__` is `customers`, matching its foreign keys, but the deployed schema must be checked/migrated accordingly.

Agent/job prices and saved-card payment amounts are stored as integer cents. Search/detail and SSE display amounts are divided by 100. The activity payment list also divides cents into dollar amounts. StripePayment holds the Pine payment record UUID, Stripe Customer ID, and Stripe PaymentMethod ID; only the Pine UUID is returned to the client for selection. Notification rows can target either a customer or merchant.

There are no migration files in this tree. Do not assume Python model changes have been applied to an existing database.

## External event and failure boundaries

`NotificationEvents` and `IncomingJobsEvents` are independent `asyncio.Event`/`Queue` managers keyed by customer ID. They work only within one Python process: events can be lost across worker restarts, are not broadcast across multiple workers, and have no persisted replay cursor. Offers are additionally cached in Redis, but there is no customer offer-recovery/list endpoint. Use a shared broker plus durable event/outbox semantics before relying on SSE across instances.

The integration boundaries include Postgres, Redis, Qdrant/OpenAI, Twilio, Stripe, arbitrary agent webhook URLs, and configured `JOB_WEBHOOK_URL`. No live dependency integration or end-to-end verification was performed for this handoff. HTTP status/error translation and transaction boundaries vary by route; review them before production rollout.

## Unmounted or incomplete areas

- `applications/customers/routes/pages/profile/` is empty/incomplete and is not included by `app.py`.
- Notification REST and GraphQL modules are placeholders and are not registered. Only notification SSE is mounted.
- `applications/customers/routes/pages/home/agent_chat.py` declares the shared home router; it does not define chat endpoints.
- Merchant route files and merchant auth modules are not registered in this app. Merchant credentials are consumed by customer webhook callback routes only.
- `landing/customers/routes/register.py` and merchant landing code define routers, but `app.py` does not include them.
- No tests were run for this documentation pass. The code still needs a source and deployed-schema audit, payment/webhook failure recovery, and live integration verification.

## Suggested next implementation handoff

1. Implement and register customer profile read/update routes with schemas and ownership checks; update the mobile profile contract at the same time.
2. Define the agent conversation API, including a customer-owned hired-agent list plus message/history transport. The current `customer_agent.py` and `routing_agent.py` files do not supply a route-backed conversation flow.
3. Complete notification history/read APIs and decide how SSE reconnect/replay works; current database rows are not exposed by a list endpoint.
4. Trace the completion callback Redis list producer (none exists in this checkout) and decide whether to implement, remove, or replace that path with a durable outbox.
5. Add migrations and verify against the deployed database, then test Stripe/Postgres/Redis/webhook failure recovery and multi-worker event delivery.

After route/schema changes, update the focused server READMEs and [`../client/mobile/README.md`](../client/mobile/README.md) from the actual implementation. Do not document planned endpoints as mounted until they are registered in `app.py`.

## Where to continue

Read the focused guides for [route registration](applications/customers/routes/README.md), [authentication routes](applications/customers/routes/auth/README.md), [home/payment](applications/customers/routes/pages/home/README.md), [agent search](applications/customers/routes/pages/search/README.md), [activity REST](applications/customers/routes/pages/activity/rest/README.md), [webhooks](applications/customers/routes/webhooks/apis/README.md), [configuration/adapters](config/README.md), [services](applications/customers/services/README.md), and [models](models/README.md). The customer mobile-side API contract is in [`../client/mobile/README.md`](../client/mobile/README.md).
