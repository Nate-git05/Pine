# Authentication screens

## Signup

The public landing-page form does not create a mobile app session. Mobile app account creation uses the SMS auth endpoint below.

`POST /auth/customer/signup` accepts:

```json
{"first_name":"Ari","last_name":"Rivera","email":"ari@example.com","phonenumber":"+15551234567"}
```

The response contains a temporary `customer_token` and a response message. The user then enters the SMS code. The phone number must satisfy the server's phone-number validator; use a normalized international number.

## Login

`POST /auth/customer/login` accepts `{"email":"ari@example.com","phonenumber":"+15551234567"}`. Its temporary verification token is named `token` (unlike signup's `customer_token`). Keep it only for the verification step.

## Verify and resend

- `POST /auth/customer/verify/{temporary_token}` with `{"code":"123456"}` verifies the code. On success, response `customer_token` is the authenticated session token. Store it securely and attach it as a Bearer token to protected calls.
- A failed code attempt returns an error. After the configured number of failures, the server sends a replacement code and returns the temporary token so verification can continue.
- `PATCH /auth/customer/verify/update/{temporary_token}` requests a replacement verification code and returns a `customer_token` field for the temporary verification flow. It is not an authenticated session token until verification succeeds.

The verification code and temporary-token lifetime are server configuration details. The current defaults are short-lived (about ten minutes); the customer session is longer-lived (about sixty days). Treat expiration responses as a request to restart or refresh the relevant auth step rather than retrying indefinitely.

## Auth header

For protected customer routes send `Authorization: Bearer <verified customer_token>`. The server validates a stored session; the token is not a JWT and should not be decoded.

`POST /auth/customer/logout` revokes the current authenticated session. The mobile client calls it with the Bearer token, then clears the token from SecureStore. If the server cannot be reached, the app still clears the local token and tells the customer that server revocation could not be confirmed.

`CustomerApi.signup()` and `CustomerApi.login()` return the temporary verification token. Pass it to `CustomerApi.verify()` with the SMS code; the client saves the verified session token through the configured `CustomerSessionStore`. The app's implementation of that interface must use secure device storage.
