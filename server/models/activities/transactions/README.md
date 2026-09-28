# Job payment history model

`JobPayments` is Pine's persisted history row for a paid agent job. It copies the job name/description, integer-cent amount, customer, hired agent, job ID/name, and paid/created timestamps. It is created after Stripe reports success; it is not a Stripe ledger, refund record, or payment reconciliation system.

The primary key is generated in Python. Database writes are separate from the Stripe charge and the `AgentJob` commit; consult the payment failure notes in the [server guide](../../../README.md#3-job-offer-saved-card-payment-and-dispatch). Check the existing database schema before applying model changes.
