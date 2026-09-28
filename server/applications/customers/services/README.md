# Customer services handoff

Shared page services live in `pages/`; authentication and webhook helpers are in sibling directories. The payment service now uses the Stripe customer ID rather than Pine's customer UUID, and reports saved card expiration while no longer assigning a tuple to the last four digits. The activity payment-list helper no longer shadows its input and completed-job dates are read from the persisted job.

Review service error translation and DB transaction boundaries when wiring the client. This pass did not exercise Stripe or database behavior.
