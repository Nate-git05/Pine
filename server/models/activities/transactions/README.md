# Transaction model notes

`JobPayments` receives generated UUIDs and declares `hired_agent_name` as a required 50-character string. This directory records application-side payment history; it is not a substitute for reconciling Stripe PaymentIntents or handling refunds.
