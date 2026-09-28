# Customer mobile app integration

This folder documents the planned React Native customer app and its integration with the customer backend in `server/`. There is no React Native source, navigation configuration, or screen implementation in this checkout yet. These READMEs describe backend-backed screens and explicitly identify missing backend capabilities; they are not evidence that those screens already exist.

Use the deployment's API origin as `API_BASE_URL`. The server does not mount an `/api/v1` prefix. For example, the auth route is `${API_BASE_URL}/auth/customer/login`.

## Navigation and API map

| Customer app page/flow | Documentation | Backend surface |
| --- | --- | --- |
| Sign up, login, verification | [Auth](routes/auth/README.md) | `/auth/customer/*` |
| Home, hired-agent conversations, incoming job cards | [Home and agent chat](routes/home-chat/README.md) | Job offer SSE exists; chat and hired-agent-list APIs are missing |
| Select/add payment method from a job card | [Payment flow](routes/payment/README.md) | `/customer/home/cards`, `/payment/add`, `/payment/{payment_id}/{offer_id}` |
| Find, inspect, hire, and fire agents | [Agent discovery](routes/search/README.md) | `/customer/search/*` |
| Requests, active/completed jobs, payment history | [Activity](routes/activity/README.md) | Activity REST and GraphQL |
| Live customer notifications | [Notifications](routes/notifications/README.md) | Notification SSE only |
| Customer profile/settings | [Profile](routes/profile/README.md) | No mounted profile API currently |

## Shared client/server conventions

- Send JSON requests with `Content-Type: application/json` unless the endpoint is an SSE stream. Paths and body fields below reflect the current server implementation.
- Authenticated customer endpoints use `Authorization: Bearer <customer_session_token>`. The session token is an opaque UUID-style value, not a JWT. Keep it in platform-secure storage and never put it in a URL.
- Signup/login verification has a temporary token stage; the verified response's `customer_token` is the session token for authenticated APIs. See [Auth](routes/auth/README.md).
- The app should handle non-2xx FastAPI responses, generally shaped as `{"detail":"..."}`. Some successful endpoints return `null`, a JSON string, or no useful body rather than a consistent response object; endpoint docs call these out.
- Use a React Native SSE implementation that can set the Bearer header. Do not put the session token in an event-stream query parameter. SSE delivery has no guaranteed replay after reconnect.
- Money values are inconsistent across surfaces: search, job detail, and incoming-offer display values are dollars, while `job_price` accepted from merchant callbacks and payment persistence use cents. Treat each endpoint's documented unit separately.

## Important missing pieces

The current server has no customer message-send/chat completion endpoint, no endpoint to list a customer's hired agents, no profile API, and no notification history/read API. The app can document the intended chat experience, but cannot complete those operations against this backend until those contracts are implemented. Incoming job offers arrive over SSE; there is no REST endpoint to recover offers missed while disconnected.

The customer webhook POST endpoints under `/customer/webhooks` are called by the agent/merchant service into Pine. They are not mobile-client endpoints. The mobile app consumes the corresponding customer SSE stream and then calls the payment endpoint.
