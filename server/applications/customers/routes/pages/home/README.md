# Customer home and payment routes

`customer_payment.py` owns saved-card listing, per-job payment, and Stripe Checkout card setup. This pass added a real empty-card response, replaced several blank details, fixed the Stripe customer ID and payment status fields, and changed Checkout to setup mode so the returned SetupIntent can identify the saved PaymentMethod. Job delivery now signs the serialized payload as a hex digest and looks up the hired agent using the customer-owned hire record.

Review payment reconciliation, refunds, and durable recovery across the Stripe/database/webhook boundary. External payment and delivery behavior was not exercised.

Card setup now builds Stripe return URLs from the request host and reuses the customer's Stripe Customer when possible. The Stripe success callback validates the checkout customer, successful SetupIntent, and exact PaymentMethod before saving it. Card list responses retrieve metadata for that exact saved PaymentMethod. The payment path accepts the `offer_id` emitted by the incoming-job SSE event.

Payment requests are serialized by a short Redis lock per customer/offer, and a successful offer result is cached to make sequential retries return without creating another job. Update the frontend to submit the SSE `offer_id` instead of the agent name in the payment URL.
