# Pine server handoff

## What this checkout contains

This branch contains a FastAPI customer backend under `server/`. The `client/` directory currently contains only a README, so this checkout does not include the customer application UI. Merchant route directories also contain placeholders and are not a complete merchant backend. Runtime configuration is loaded from `server/.env`; never commit that file or copy credentials into handoff notes.

## How the server is organized

- `app.py` owns the FastAPI lifespan, shared clients, and customer route registration. `dependencies.py` contains the request-scoped getters for app state such as database sessions, API clients, and event managers.
- `config/` builds the Postgres, Redis, and Qdrant adapters and loads environment settings.
- `applications/customers/routes/` contains auth, agent search/hire, payment, activity, notification, GraphQL, and webhook endpoints.
- `applications/customers/services/` contains shared customer operations.
- `models/` defines SQLAlchemy records. UUID defaults are generated in Python.
- `landing/` has initial customer and merchant registration endpoints.

## Changes in this pass

- Fixed the relational database app-state spelling and Redis cache list awaits; the cache port is converted from its environment string to an integer.
- Added a default `agents` Qdrant collection name and made collection creation safe when the collection already exists. Vector inserts now attach payloads to each point, and delete queries pass point objects to the ID helper.
- Registered the customer auth, home/payment, search, activity REST and GraphQL, notification REST/GraphQL/SSE, and webhook routers with FastAPI.
- Fixed search request embedding input, cursor handling, async helper calls, route declaration, agent description lookup, and rating calculation when no jobs have ratings.
- Fixed activity helper mistakes, job/customer relationship keys, and UUID generation defaults. Stripe payment setup now uses Checkout setup mode and looks up the saved payment method from the SetupIntent.
- Kept incoming job offers and customer notifications on separate event channels, with customer-keyed queues within each channel. Both SSE inner loops also compare each dequeued payload's customer ID with the authenticated customer before yielding it. Aligned pending-offer Redis writes/reads and fixed merchant callback authentication, ownership checks, request fields, and signatures.
- Added readable details for a number of customer errors and corrected several payment and activity response fields.

## Current caveats for the next agent

- This was a source review and targeted repair, not an end-to-end verification against live Postgres, Redis, Qdrant, Stripe, OpenAI, or Twilio services. No tests were run.
- Changing `Customer.__tablename__` to `customers` aligns it with the foreign keys declared throughout these models. Confirm the deployed database table name and apply a migration if it currently uses `customer`.
- Existing model/schema mismatches and incomplete flows remain outside this pass. Review merchant registration and routes, profile wiring, payment idempotency and refunds, webhook authentication, and Stripe return URL configuration before production use.
- Profile REST and GraphQL modules remain empty or incomplete in this checkout. Customer notification REST, GraphQL, and SSE routes are registered.
- Event queues are in process memory. Multiple server workers or instances will not share events. Move event fanout to Redis pub/sub or another shared broker before relying on this across workers.
- Inspect `git diff` before committing, and do not expose `server/.env` values in logs or docs.

## Local entry point

The ASGI object is `server.app:app`. Startup requires the environment variables validated in `config/configuration.py` and reachable external services. Dependency pins are in `requirements.txt`.

See the directory READMEs beside the edited code for focused handoff notes.

## Activity GraphQL pagination

The activity GraphQL endpoint is `/customer/activity`. Each resolver receives the authenticated customer and database session through `get_customer_context`. To request a later page, send request-level `cursor: true` and `last_id_seen` containing the prior response's list-specific timestamp as ISO-8601. The context converts that string into a timezone-aware `datetime`; resolvers apply it alongside the customer's ID and the relevant job/request/payment state. Each list fetches one extra row to tell the client whether another page is available. The same request-level cursor applies to every selected field, so paginate one activity list per request. The output timestamp fields are `lastRequestDate`, `lastJobDate`, or `lastPaymentDate` after Strawberry camel-casing.

## Additional fixes in the current working changes

- Incoming job offers now receive a unique `offer_id`; the ID is included in the job-offer SSE event and is used by the payment route. The client should call `POST /customer/home/payment/{saved_payment_id}/{offer_id}` after card selection.
- Stripe card setup reuses an existing Stripe Customer, builds valid return URLs from the request host, and saves the exact PaymentMethod returned by a successful SetupIntent. Saved card details are retrieved for that exact PaymentMethod.
- PaymentIntent creation uses a stable idempotency key per offer and selected saved method. A short Redis lock serializes payment submissions for an offer; declined offers remain available, and successful offers are consumed after Pine records the job and payment.
- Fixed SMS verification hash checking and incorrect-code fallthrough, login verification/customer lookup, session-token response, duplicate signup checks, and name-field validators.
- Fixed the request-answer schema import and response validation; answered requests are marked handled only after the merchant endpoint accepts the answer. Customer job ratings now require a completed, unrated job.
- Updated GraphQL customer context authentication to use the same HTTP Bearer token extraction and HMAC session validation as REST. The pathless `HTTPBearer` dependency avoids tying token extraction to a token-issuing route. The context validates JSON request data through the auth schema, reads `cursor` and `last_id_seen` from the request or GraphQL variables, and returns `None` for either field when it is absent. Activity resolvers apply those values with their own customer and state filters.
- Notification SSE events now include the persisted notification type with the notification ID, header, and message. The signed job request sent to an agent now includes the `agent_restrictions` saved when the customer hired that agent.

## Notification and incoming-job SSE flow

`NotificationEvents` and `IncomingJobsEvents` have separate event managers. Each manager routes an event to a queue keyed by its `customer_id`; the SSE handler waits on that customer's event, reads the queued payload, and verifies its customer ID against the authenticated session before yielding it. The payload ID check is a second guard after queue routing. The event remains set while that customer's queue contains items and is cleared when it becomes empty. These queues live in one process and do not fan events out between multiple workers or multiple simultaneous SSE subscribers for the same customer.

The Stripe charge, database writes, and merchant webhook are still separate systems without a reconciliation worker or durable outbox. A failure after charging may require recovery; idempotency prevents repeating the same Stripe operation but does not make the full workflow atomic. No external-service verification was performed for these changes.
