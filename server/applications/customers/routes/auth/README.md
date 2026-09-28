# Customer authentication routes

The end-to-end auth/session lifecycle is in [`server/README.md`](../../../../README.md#1-signup-and-session-authentication). All four handlers share the router created in `signup.py` and mounted at `/auth/customer`.

| Route | Behavior |
| --- | --- |
| `POST /signup` | Check duplicate email/phone, store pending verification state, send an SMS code, return a temporary token. |
| `POST /login` | Match email and phone, send a code, return a temporary token. |
| `POST /verify/{temporary_token}` | Check the code; create the customer on signup or load it on login; create a hashed, expiring session. |
| `PATCH /verify/update/{temporary_token}` | Issue and send a replacement code for the pending flow. |

The successful verify response's `customer_token` is the Bearer session token. Signup's temporary token is also named `customer_token`, while login's is named `token`; distinguish by flow stage. Verification data uses Redis's default 600-second expiration, codes are stored as bcrypt hashes, and three bad code attempts trigger a replacement code. The session token is a random UUID whose HMAC hash is stored in Postgres; default session duration is 60 days.

These handlers do not provide logout, session refresh, account recovery, or phone-number-change routes. Each request depends on working Postgres/Redis/Twilio configuration.
