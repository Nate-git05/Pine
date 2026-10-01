# Pine web applications

This directory contains the Next.js web frontend. The App Router separates public landing pages from signed-in application areas:

- `/` and `/landing/customer` are the customer landing page.
- `/landing/merchant` is reserved for the merchant landing page.
- `/application/customer` and `/application/merchant` are reserved for the two web application areas.

The customer Register form creates a customer account through the existing SMS verification flow. It posts the four registration fields to `/api/auth/customer/signup`, which forwards them to FastAPI `POST /auth/customer/signup`. After the customer enters the SMS code, `/api/auth/customer/verify` forwards it to `POST /auth/customer/verify/{customer_token}`. A successful verification stores the returned session token in an HTTP-only, same-site cookie. Merchant registration is a separate flow; its model and routes are not implemented yet, so customer registration data must not be sent to merchant endpoints.

The web server reads `PINE_API_BASE_URL`; local development defaults to `http://localhost:8000`, and deployed environments must set it to the backend origin. The backend must be running with its Postgres, Redis, and SMS configuration for account registration to complete. The separate public lead endpoint `POST /landing/register/customer` remains available for waitlist-style registration.

Install dependencies with `npm install`, then run `npm run dev` from this directory.
