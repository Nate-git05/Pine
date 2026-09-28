# User models

`Customer` stores customer name, unique email/phone, and audit timestamps. Its table name is `customers`, matching foreign keys used by job, payment, and hire models. `Merchant` stores merchant identity and its image key; merchant auth credentials are stored separately in `MerchantAPI`.

Customer auth and data ownership are described in the [server guide](../../README.md#1-signup-and-session-authentication). Both identity models generate UUIDs in Python, but verify deployed table names, constraints, and existing records before migration or rollout.
