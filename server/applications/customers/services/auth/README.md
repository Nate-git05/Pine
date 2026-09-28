# Customer authentication service

`auth_service.py` supplies the six-digit code generator and Twilio SMS sender, `AuthState`, REST's `get_current_customer` dependency, and GraphQL's `get_customer_context`. Both request types validate the UUID Bearer token by HMAC-hashing it with the Pine server secret and looking up its Postgres session record; session expiry is checked and `validated_at` is updated on use.

Signup/login temporary tokens and flow data live in Redis; the final session token is not stored in plaintext. GraphQL parses Authorization itself because Strawberry context construction differs from the REST dependency path, then supplies customer and SQLAlchemy session to resolvers. See the [auth route guide](../../routes/auth/README.md) for the lifecycle. No logout/revocation endpoint is registered.
