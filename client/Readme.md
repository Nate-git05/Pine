# Client applications

- [`mobile/`](mobile/README.md) contains the customer React Native app's route-by-route backend integration guide.
- [`web/`](web/README.md) contains the Next.js customer and merchant web applications, including their landing and application route areas.

Customer account registration uses the customer auth flow: `POST /auth/customer/signup`, then SMS verification at `POST /auth/customer/verify/{customer_token}`. `POST /landing/register/customer` is a separate lead-registration endpoint and does not create an account. Merchant registration has a separate model and is not implemented in the server yet.
