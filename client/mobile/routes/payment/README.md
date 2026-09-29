# Job payment flow

This is a customer-app flow launched by tapping the job offer card in an agent conversation. Preserve the `offer_id` from the incoming job-offer SSE event for the entire flow.

## 1. Load saved cards

Call authenticated `GET /customer/home/cards`. A successful response has a `payments_lst` array. Each item includes Pine's `payment_id`, `payment_last4`, `payment_card_type`, and `expires_at` (`MM/YYYY`). An empty array means no saved cards. The app sends the returned Pine `payment_id` to the charge endpoint; it does not send a raw Stripe PaymentMethod ID.

## 2. Add a card when needed

Call authenticated `POST /customer/home/payment/add`. The handler returns a Stripe Checkout setup URL directly (the HTTP response is serialized as a JSON string). Open it using the platform browser/Stripe Checkout flow. Stripe returns through `/customer/home/payment/add/success` or `/failed`; on return, refresh `/cards` and let the customer select the newly saved card. The success callback is not proof that a particular job was paid; card setup and job payment are separate actions.

## 3. Confirm selected card and pay this offer

Call authenticated `POST /customer/home/payment/{payment_id}/{agent_id}/{offer_id}` with no JSON body. Use the Pine saved-card ID from `/cards`, the hired-agent ID from the offer event, and that event's exact offer ID. On success the backend charges the saved method, creates the job/payment records, calls the agent webhook, and creates customer and merchant notifications. The current success body is a response message, not a job detail object.

Before the customer confirms, show the amount and selected card (brand and last four digits) so they can verify which method will be charged. After they confirm, set a processing state and disable the Pay button and card selection until the request finishes. This prevents accidental duplicate taps in the app; it is a frontend interaction rule, not a backend payment lock.

The backend validates that the saved card belongs to this customer, the offer belongs to this customer and selected hired agent, and the agent is active. Stripe idempotency keys are stable for the same customer, offer, and saved card, so a retry with the same offer and card reuses the Stripe payment attempt. The backend does not acquire a Redis lock. Declined offers remain available; successful offers are removed after Pine records the job and payment.

## Error and recovery behavior

Display server `detail` messages in a user-friendly way and preserve the offer and selected card when retrying. If the request times out or the connection drops, keep the payment result in an uncertain/pending state and retry only with the same offer and card; don't let the customer switch cards while that result is unresolved. If the server says the offer was already processed, refresh activity and look for the resulting job. If a charge succeeds but a later database/webhook step fails, the full flow is not transactional and there is no durable reconciliation/outbox worker in this checkout. The client cannot infer success from a network timeout alone; provide a recovery/support path rather than encouraging repeated attempts with a different card.

The Stripe charge, database commit, agent callback, and notifications are separate operations. This is a documented backend limitation, not a mobile retry policy the client can repair.
