# Pine web applications

This directory contains the Next.js web frontend. The App Router separates public landing pages from signed-in application areas:

- `/` and `/landing/customer` are the customer landing page.
- `/landing/merchant` is reserved for the merchant landing page.
- `/application/customer` and `/application/merchant` are reserved for the two web application areas.

Customer landing-page registration records a lead in the customer registration table through `/api/landing/register/customer` → `POST /landing/register/customer`. Merchant landing-page registration records a lead in the separate merchant registration table through `/api/landing/register/merchant` → `POST /landing/register/merchant`. Both forms collect first name, last name, email, and phone; they do not create authenticated application accounts.

Customer app account signup is a separate SMS verification flow: `POST /auth/customer/signup`, then `POST /auth/customer/verify/{customer_token}`. The React Native API integration guide is in [`../mobile/README.md`](../mobile/README.md). The web server reads `PINE_API_BASE_URL`; local development defaults to `http://localhost:8000`, and deployed environments must set it to the backend origin. Landing registrations require the backend and Postgres to be available.

Install dependencies with `npm install`, then run `npm run dev` from this directory.
