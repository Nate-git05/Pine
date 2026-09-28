# Customer service layer

Services hold operations reused by route handlers; they are not a separate HTTP layer. The route handler usually owns input validation, dependency injection, and the ordering of database/external side effects. Service functions may call Stripe, query Postgres, or create records needed for those flows.

- `auth/auth_service.py`: SMS code creation/sending, customer REST authentication, and GraphQL customer context.
- `pages/search_service.py`: transforms Qdrant payloads into search results and calculates aggregate ratings from completed jobs.
- `pages/home_service.py`: retrieves Stripe card metadata, charges an off-session PaymentIntent, creates job/payment records, and resolves an agent webhook URL.
- `pages/activity_service.py`: formats activity lists and resolves the agent/merchant signing information used to send request responses.
- `webhooks/webhook_service.py`: merchant API-key lookup, HMAC signature access, callback ownership checks, and notification/callback helpers.

Business flows are not atomic across services: Stripe, Postgres, Redis, outbound HTTP, and SSE can each succeed/fail separately. See [`server/README.md`](../../../README.md) for ordering and recovery caveats. No live integration verification is recorded for these operations.
