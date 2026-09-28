# Home and agent conversations

## Product intent

The home page is the blank starting state before an agent is hired. After hiring, the intended experience is a GPT/Claude-style conversation with that agent. A job offer from an agent should appear as a clickable message/card in that conversation. Selecting it opens the [payment flow](../payment/README.md).

## What the backend currently supports

There is no mounted endpoint to list hired agents, load chat history, send a free-form customer message, or receive an agent's conversational reply. `POST /customer/search/agent/hire/{agent_id}` creates a hire, but no customer-facing list endpoint returns those hires for home-page bootstrap. The `agent_chat.py` route module is empty. These are backend gaps; the app cannot implement a working conversation lifecycle from the current API alone.

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
