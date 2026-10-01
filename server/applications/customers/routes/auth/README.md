# Customer authentication routes

Signup, login, verification, and logout handlers attach to the shared `customer_auth_router`. `app.py` imports the sibling modules so all handlers are registered. Verification error responses now include a useful message where one was blank. Review bearer token parsing, SMS throttling, and verification token expiry as a separate authentication hardening pass.

## Logout

`POST /auth/customer/logout` requires the verified customer Bearer token. It deletes the matching session row for that customer, revoking only the current device session. Other sessions for the same customer remain active. After this route succeeds, the client removes the token from secure storage.
