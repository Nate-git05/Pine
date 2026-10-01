# Pine server handoff

## What this checkout contains

This branch contains a FastAPI customer backend under `server/`. The `client/mobile/` directory contains customer integration documentation but no React Native source or navigation/screens. The `client/web/` directory is intended for the merchant Next.js app and has no app source in this checkout. Merchant route directories also contain placeholders and are not a complete merchant backend. Runtime configuration is loaded from `server/.env`; never commit that file or copy credentials into handoff notes.

## How the server is organized

- `app.py` creates the FastAPI app and registers customer routers. `lifespan.py` owns startup and shutdown of shared clients and application state. `dependencies.py` contains request-scoped getters for that shared state.
- `config/` builds the Postgres, Redis, and Qdrant adapters and loads environment settings.
- `applications/customers/routes/` contains auth, agent search/hire, payment, activity, notification, GraphQL, and webhook endpoints.
- `applications/customers/services/` contains shared customer operations.
- `models/` defines SQLAlchemy records. UUID defaults are generated in Python.
- `landing/` has initial customer and merchant registration endpoints.

## Changes in this pass

- Fixed the relational database app-state spelling and Redis cache list awaits; the cache port is converted from its environment string to an integer.
- Added a default `agents` Qdrant collection name and made collection creation safe when the collection already exists. Vector inserts now attach payloads to each point, and delete queries pass point objects to the ID helper.
- Registered the customer auth, home/payment, search, activity REST and GraphQL, SSE, and webhook routers with FastAPI.
- Fixed search request embedding input, cursor handling, async helper calls, route declaration, agent description lookup, and rating calculation when no jobs have ratings.
- Fixed activity helper mistakes, job/customer relationship keys, and UUID generation defaults. Stripe payment setup now uses Checkout setup mode and looks up the saved payment method from the SetupIntent.
- Kept incoming job offers and customer notifications on separate event channels, with customer keyed queues within each channel. Aligned pending-offer Redis list writes/reads and fixed merchant callback authentication, ownership checks, request fields, and signatures.
- Added readable details for a number of customer errors and corrected several payment and activity response fields.

## Current caveats for the next agent

- This was a source review and targeted repair, not an end-to-end verification against live Postgres, Redis, Qdrant, Stripe, OpenAI, or Twilio services. No tests were run.
- Changing `Customer.__tablename__` to `customers` aligns it with the foreign keys declared throughout these models. Confirm the deployed database table name and apply a migration if it currently uses `customer`.
- Existing model/schema mismatches and incomplete flows remain outside this pass. Review merchant registration and routes, profile/notification GraphQL wiring, payment idempotency and refunds, webhook authentication, and Stripe return URL configuration before production use.
- Profile REST and notification REST/GraphQL modules are empty or incomplete in this checkout. The profile GraphQL module is also unfinished. Do not assume those surfaces are available because the related folders exist.
- Event queues are in process memory. Multiple server workers or instances will not share events. Move event fanout to Redis pub/sub or another shared broker before relying on this across workers.
- Inspect `git diff` before committing, and do not expose `server/.env` values in logs or docs.

## Local entry point

The ASGI object is `server.app:app`. Startup requires the environment variables validated in `config/configuration.py` and reachable external services. Dependency pins are in `requirements.txt`.

See the directory READMEs beside the edited code for focused handoff notes.

## Customer mobile API contract

The customer app route-by-route contract is documented in [`client/mobile/README.md`](../client/mobile/README.md), including auth, search/hire, job-offer SSE and payment, activity, notifications, and profile gaps. The customer API has no `/api/v1` prefix. The mobile docs are based on routes registered in `app.py`, not on a checked-in client implementation.

Key implementation boundaries for the mobile app:

- Agent/merchant services POST incoming offers to Pine at `/customer/webhooks/client`; the mobile app consumes authenticated `/customer/webhooks/client/event` and must retain the event's `offer_id` for the payment route. The webhook POST is not a mobile API.
- Customer chat message send/history and a hired-agent list endpoint are not implemented. `agent_chat.py` is empty, so the intended conversation UI cannot yet be fully backed by this server.
- Customer notification SSE exists, but notification REST/GraphQL history routes and profile APIs are not mounted. Event queues are process-local and do not replay missed events.
- `GET /customer/home/cards`, `POST /customer/home/payment/add`, and `POST /customer/home/payment/{payment_id}/{offer_id}` form the saved-card/job-offer payment path. The payment route requires the exact saved-card ID and offer ID.

## Additional fixes in the current working changes

- Incoming job offers now receive a unique `offer_id`; the ID is included in the job-offer SSE event and is used by the payment route. The client should call `POST /customer/home/payment/{saved_payment_id}/{offer_id}` after card selection.
- Stripe card setup reuses an existing Stripe Customer, builds valid return URLs from the request host, and saves the exact PaymentMethod returned by a successful SetupIntent. Saved card details are retrieved for that exact PaymentMethod.
- PaymentIntent creation uses a stable idempotency key per offer and selected saved method. A short Redis lock serializes payment submissions for an offer; declined offers remain available, and successful offers are consumed after Pine records the job and payment.
- Fixed SMS verification hash checking and incorrect-code fallthrough, login verification/customer lookup, session-token response, duplicate signup checks, and name-field validators.
- Fixed the request-answer schema import and response validation; answered requests are marked handled only after the merchant endpoint accepts the answer. Customer job ratings now require a completed, unrated job.
- Fixed GraphQL customer context authentication and several activity pagination/query errors.

The Stripe charge, database writes, and merchant webhook are still separate systems without a reconciliation worker or durable outbox. A failure after charging may require recovery; idempotency prevents repeating the same Stripe operation but does not make the full workflow atomic. No external-service verification was performed for these changes.
