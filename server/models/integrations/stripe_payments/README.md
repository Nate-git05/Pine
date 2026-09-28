# Stripe payment record notes

Saved payment records now generate UUIDs and allow `last_used` to remain empty until a card is used. The stored `stripe_payment_id` should refer to the SetupIntent's PaymentMethod ID. Validate legacy records and update the database schema if required.
