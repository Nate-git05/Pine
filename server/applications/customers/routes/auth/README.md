# Customer authentication routes

Signup, login, and verification handlers attach to the shared `customer_auth_router`. `app.py` imports the sibling modules so all three sets of handlers are registered. Verification error responses now include a useful message where one was blank. Review bearer token parsing, SMS throttling, and verification token expiry as a separate authentication hardening pass.
