# Customer home and payment routes

`customer_payment.py` owns saved-card listing, per-job payment, and Stripe Checkout card setup. This pass added a real empty-card response, replaced several blank details, fixed the Stripe customer ID and payment status fields, and changed Checkout to setup mode so the returned SetupIntent can identify the saved PaymentMethod. Job delivery now signs the serialized payload as a hex digest and looks up the hired agent using the customer-owned hire record.

Review payment idempotency, the setup success/cancel URL source, Stripe webhook reconciliation, and database compensation. External payment and delivery behavior was not exercised.
