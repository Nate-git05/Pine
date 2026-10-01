-- Run once against the existing Postgres database before deploying the Stripe flow update.
-- This project does not currently run migrations automatically at startup.

ALTER TABLE customers
    ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(100);

-- Reuse a Stripe customer already referenced by one of this customer's saved cards.
UPDATE customers AS customer
SET stripe_customer_id = saved_payment.stripe_customer_id
FROM (
    SELECT DISTINCT ON (customer_id)
        customer_id,
        stripe_customer_id
    FROM stripe_payments
    WHERE stripe_customer_id IS NOT NULL
    ORDER BY customer_id, last_used DESC NULLS LAST, created_at DESC NULLS LAST
) AS saved_payment
WHERE customer.id = saved_payment.customer_id
  AND customer.stripe_customer_id IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_customers_stripe_customer_id
    ON customers (stripe_customer_id)
    WHERE stripe_customer_id IS NOT NULL;

ALTER TABLE job_payments
    ADD COLUMN IF NOT EXISTS offer_id UUID,
    ADD COLUMN IF NOT EXISTS stripe_payment_intent_id VARCHAR(100),
    ADD COLUMN IF NOT EXISTS dispatched_at TIMESTAMPTZ;

CREATE UNIQUE INDEX IF NOT EXISTS uq_job_payments_offer_id
    ON job_payments (offer_id)
    WHERE offer_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_job_payments_payment_intent_id
    ON job_payments (stripe_payment_intent_id)
    WHERE stripe_payment_intent_id IS NOT NULL;
