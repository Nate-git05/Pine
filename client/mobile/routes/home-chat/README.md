# Home and agent conversations

## Product intent

The home page is the blank starting state before an agent is hired. After hiring, the intended experience is a GPT/Claude-style conversation with that agent. A job offer from an agent should appear as a clickable message/card in that conversation. Selecting it opens the [payment flow](../payment/README.md).

## Send a chat message

Call authenticated `POST /customer/home/chat/{hired_agent_id}` with the hired-agent row ID (the ID returned when the customer hires an agent), not the public agent ID:

```json
{"customer_message":"Can you help me plan this task?"}
```

The response is `{"response":"..."}`. The server verifies that the hire belongs to the signed-in customer and is active. Router and tooling context are stored separately in Redis for that customer and hired-agent pair. There is no endpoint to list a customer's hires or retrieve chat history, so the app must get the hired-agent ID from the hire response or another available app state source. Do not assume the backend can bootstrap the home screen's hired-agent list after a fresh install or sign-in.

The chat route uses a router agent and a tooling agent with classification-specific skill instructions. Tool implementations and job submission from chat are not wired yet; this endpoint returns an agent response but does not create a job or payment.

## Incoming job offers

Connect to authenticated `GET /customer/webhooks/client/event` using a React Native SSE client that supports the Authorization header. A job-offer event includes:

```json
{
  "offer_id":"<uuid>",
  "agent_name":"Research Agent",
  "agent_id":"<uuid>",
  "job_name":"Market scan",
  "job_description_str":"Review the target market",
  "job_price":25.0
}
```

Render the agent and job fields in the message card. Keep `offer_id` as the action identifier; pass that exact ID into payment. Do not use the agent ID as the payment identifier. `job_price` in the event is displayed in dollars, while server-side offer input/payment handling uses cents.

The event queue is in process memory, so a disconnected client may miss an offer and another server worker may not see it. There is no pending-offer list or replay API currently. The backend gives pending offers a limited lifetime; show a useful expired/unavailable state if payment reports that an offer can no longer be used.

## Notifications versus offers

Customer notification events use a separate authenticated stream, `GET /customer/notifications/events`. Do not treat notifications as job-offer actions: the offer stream carries the `offer_id` needed to pay. See [Notifications](../notifications/README.md).
