# Authentication and API credential models

- `SMSVerification` stores pending/accepted customer signup or login verification. The six-digit code is bcrypt-hashed; the raw code is not readable from the model.
- `SessionAuthentication` stores an HMAC hash of a customer's opaque UUID session token, expiry, and validation timestamps. The plaintext token is returned once at verification and is not stored in the session row.
- `MerchantAPI` stores an API key and merchant webhook secret. Its helper creates/checks hex HMAC-SHA256 signatures over the exact serialized request body.

The customer auth lifecycle and callback signing boundaries are covered in the [server guide](../../README.md#1-signup-and-session-authentication) and [webhook guide](../../applications/customers/routes/webhooks/apis/README.md). Confirm column types and enum values against the database schema before rollout.
