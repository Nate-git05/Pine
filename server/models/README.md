# Server persistence models

SQLAlchemy table models are grouped by domain. UUIDs are generated in Python for most primary keys. The [end-to-end server guide](../README.md#persistence-and-money-conventions) explains when records are written in each customer flow.

- `users/`: customer and merchant identity records.
- `auths/`: SMS verification records, hashed customer sessions, and merchant API credentials/signing helpers.
- `agents/`: public agents and customer-specific `HiredAgent` contracts/states.
- `activities/jobs/`: `AgentJob` and agent-created `AgentJobRequest` records.
- `activities/transactions/`: application-side `JobPayments` history; not the Stripe source of truth.
- `integrations/stripe_payments/`: customer's Stripe Customer/PaymentMethod references behind a Pine saved-payment UUID.
- `notifications/`: notification rows for customers and merchants.

There are no migration files in this tree. `Customer.__tablename__` is `customers` because the other model foreign keys target `customers.id`; verify the deployed database and migrate it if needed. Model declarations and a running database schema can differ, so compare them before rollout.
