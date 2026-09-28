# Customer home and payment routes

The `/customer/home` router is declared in `agent_chat.py`; despite that filename, the module currently contains no chat endpoints. `customer_payment.py` attaches payment handlers to it. The end-to-end offer-to-payment sequence and recovery limits are documented in [`server/README.md`](../../../../../README.md#3-job-offer-saved-card-payment-and-dispatch).

## Current handlers

- `GET /cards`: return saved Pine card IDs and display metadata. Stripe is queried for each stored PaymentMethod; raw Stripe IDs are not the client selector.
- `POST /payment/add`: create Stripe Checkout setup mode and return its URL.
- `GET /payment/add/success` and `/payment/add/failed`: handle the Stripe browser return and save a verified setup PaymentMethod on success.
- `POST /payment/{payment_id}/{offer_id}`: lock and validate the customer's selected card and offer, charge off-session through Stripe, create job/payment records, forward the job to the agent, persist notifications, then publish a customer notification event.

The incoming offer SSE has a Pine-generated `offer_id`; it must be used in the payment path. Offer data expires from Redis after 15 minutes. A Redis lock and Stripe idempotency key help prevent duplicate work, but the charge, separate database commits, agent callback, and notification publication are not one atomic transaction. Post-charge errors require checking Activity before retrying; there is no reconciliation/outbox or refund route in this code.

See [home schemas](../../../schemas/pages/home_schemas.py) and the [client payment integration guide](../../../../../../client/mobile/routes/payment/README.md) for response contracts.
