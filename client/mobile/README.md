# Customer mobile app integration

This folder contains the Expo Router React Native customer app, API transport layer, and route-by-route integration guide. `src/api/customer-api.ts` wraps customer routes mounted by `server/app.py`.

## Run the mobile app

Use Node.js 22.13 or newer. Copy `.env.example` to `.env` in this directory and point it at the running customer server:

```env
EXPO_PUBLIC_PINE_API_URL=http://YOUR_LOCAL_NETWORK_IP:8000
EXPO_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_replace_me
```

Use your development machine's LAN IP when testing on a physical phone; `localhost` on the phone points back to the phone itself. Install the dependencies with `npm install`, then run `npm start` in a custom development build. Stripe's native SDK is not available in Expo Go. The publishable key is safe for the mobile app; never put a Stripe secret/restricted key in `EXPO_PUBLIC_*` variables.

For the browser preview, run `npm run web`. The API allows `http://localhost:8081` and `http://127.0.0.1:8081` by default. If you open the preview through a forwarded workspace URL, add that exact browser origin to `PINE_CLIENT_ORIGINS` in `server/.env` as well as setting `EXPO_PUBLIC_PINE_API_URL` to a backend URL the browser can reach, then restart both servers.

The app shell uses Expo Router and stores the verified customer session with Expo SecureStore. `src/api/mobile-session.ts` adapts SecureStore and the native SSE client to the framework-independent `CustomerApi`.

## Visual direction

Mobile screens share the customer landing page colors: cream `#FBF3E9`, paper white `#FFFAF4`, sand `#F4EAE0`, taupe `#D9C6B9`, coral `#DBA895`, and wine `#742239`. The launch wordmark uses taupe on white; primary actions use wine for a stronger, readable color pop.

The app currently includes SMS signup/login/verification, agent discovery and hiring, agent chat, streamed job offers with saved-card payment selection, activity lists, notification inbox, profile, email integrations, hire management, and local sign out. The backend does not provide chat history or job-offer replay, so chat messages and offers cannot be restored after the app loses that in-memory state.

Create one `CustomerApi` instance with the deployment's API origin and a `CustomerSessionStore` adapter backed by the secure-storage library selected for the app. The server does not mount an `/api/v1` prefix. For example, the auth route is `${API_BASE_URL}/auth/customer/login`.

```ts
import { CustomerApi } from './src/api';

const customerApi = new CustomerApi({
  baseUrl: API_BASE_URL,
  sessionStore: secureCustomerSessionStore,
});
```

The API client wraps auth, search/hire, chat, payments, activity, notifications, profile, and Gmail integration routes. It stores the verified session token through the injected secure store. The app supplies a React Native SSE adapter that sends the required Bearer header.

## Navigation and API map

| Customer app page/flow | Documentation | Backend surface |
| --- | --- | --- |
| Sign up, login, verification | [Auth](routes/auth/README.md) | `/auth/customer/*` |
| Home, hired-agent conversations, incoming job cards | [Home and agent chat](routes/home-chat/README.md) | Chat reply, hired-agent GraphQL lists, and job-offer SSE |
| Select/add payment method from a job card | [Payment flow](routes/payment/README.md) | `/customer/home/cards`, `/payment/add`, `/payment/{payment_id}/{agent_id}/{offer_id}`, `/payment/confirm/{payment_intent_id}` |
| Find, inspect, hire, and fire agents | [Agent discovery](routes/search/README.md) | `/customer/search/*` |
| Requests, active/completed jobs, payment history | [Activity](routes/activity/README.md) | Activity REST and GraphQL |
| Live notifications and notification inbox | [Notifications](routes/notifications/README.md) | SSE, GraphQL unread list, REST detail/read, and clear unread routes |
| Customer profile/settings | [Profile](routes/profile/README.md) | `/profile/*`, `/customer/profile/*` |

## Shared client/server conventions

- Send JSON requests with `Content-Type: application/json` unless the endpoint is an SSE stream. Paths and body fields below reflect the current server implementation.
- Authenticated customer endpoints use `Authorization: Bearer <customer_session_token>`. The session token is an opaque UUID-style value, not a JWT. Keep it in platform-secure storage and never put it in a URL.
- Signup/login verification has a temporary token stage; the verified response's `customer_token` is the session token for authenticated APIs. See [Auth](routes/auth/README.md).
- The app should handle non-2xx FastAPI responses, generally shaped as `{"detail":"..."}`. Some successful endpoints return `null`, a JSON string, or no useful body rather than a consistent response object; endpoint docs call these out.
- Use a React Native SSE implementation that can set the Bearer header. Do not put the session token in an event-stream query parameter. SSE delivery has no guaranteed replay after reconnect.
- Money values are inconsistent across surfaces: search, job detail, and incoming-offer display values are dollars, while `job_price` accepted from merchant callbacks and payment persistence use cents. Treat each endpoint's documented unit separately.

## Current backend scope and gaps

The server has a customer chat completion route at `POST /customer/home/chat/{hired_agent_id}`. Active/fired hires can be listed through customer profile GraphQL, but there is no endpoint to retrieve chat history. The agent tool implementations are not wired yet, so chat does not submit jobs. Incoming offers arrive over SSE and cannot be recovered through a REST list after a disconnect.

Customer notifications have an authenticated SSE stream, an unread-notification GraphQL query, a REST detail route that marks one notification read, and a REST route that marks supplied notification IDs read. See [Notifications](routes/notifications/README.md) for the current contract.

The customer webhook POST endpoints under `/customer/webhooks` are called by the agent/merchant service into Pine. They are not mobile-client endpoints. The mobile app consumes the corresponding customer SSE stream and then calls the payment endpoint with the offer ID from that event.
