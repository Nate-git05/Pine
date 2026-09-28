# Customer page schemas

These Pydantic and Strawberry types define payloads/responses for mounted search, payment, activity, and notification SSE routes. They are contracts, not proof a matching route is mounted: profile schemas exist but profile routes are incomplete and not included by `app.py`; notification REST/GraphQL schemas likewise do not provide history endpoints.

Notable conventions:

- Search/detail and activity prices are exposed in dollars, while persisted job prices are integer cents.
- `ReturnedPayments.payment_id` is Pine's UUID for a saved Stripe method, not Stripe's PaymentMethod ID.
- Activity GraphQL uses Strawberry's default camel-casing; the request timestamp field is currently misspelled `rrequest_created_at` in Python, producing the same misspelling in GraphQL.
- Incoming job webhook `job_price` is a positive integer in cents; its SSE output is a display value in dollars and includes generated `offer_id`.

For routes and data flow, see [`server/README.md`](../../../../README.md) and the [customer mobile API guide](../../../../../client/mobile/README.md).
