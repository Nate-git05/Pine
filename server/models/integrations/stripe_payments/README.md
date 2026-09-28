# Saved Stripe payment model

`StripePayment` maps a customer-owned saved payment method. It stores a Pine-generated UUID used by customer routes, the Stripe Customer ID, the Stripe PaymentMethod ID, and audit fields. The PaymentMethod reference is taken from a successful SetupIntent; it is used for card display lookup and off-session job charges.

The customer sends the Pine UUID from `GET /customer/home/cards`, never the raw Stripe ID. This table does not represent a job charge; job payment history is in `JobPayments`. See [home/payment](../../../applications/customers/routes/pages/home/README.md) and validate deployed schema/legacy records before rollout.
