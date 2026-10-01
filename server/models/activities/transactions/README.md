# Transaction model notes

`JobPayments` records the unique offer ID, Stripe PaymentIntent ID, and dispatch timestamp alongside the job/customer/hired-agent references. This lets Pine recover a successful charge without creating another payment row or job after a retry. Apply the SQL update in `server/migrations/2026-10-01-stripe-job-payment-recovery.sql` before deploying these model fields. Payment history still needs explicit refund handling and reconciliation for disputes.
