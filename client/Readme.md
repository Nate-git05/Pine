# Client applications

- [`mobile/`](mobile/README.md) contains the customer React Native app's route-by-route backend integration guide.
- [`web/`](web/README.md) contains the Next.js customer and merchant web applications, including their landing and application route areas.

The customer and merchant landing forms collect the same contact fields but write to separate registration models through `POST /landing/register/customer` and `POST /landing/register/merchant`. Customer account creation for the mobile app is a separate SMS auth flow: `POST /auth/customer/signup`, then `POST /auth/customer/verify/{customer_token}`.
