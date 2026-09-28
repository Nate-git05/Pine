# Job payment flow

This is a customer-app flow launched by tapping the job offer card in an agent conversation. Preserve the `offer_id` from the incoming job-offer SSE event for the entire flow.

## 1. Load saved cards

Call authenticated `GET /customer/home/cards`. A successful response has a `payments_lst` array. Each item includes Pine's `payment_id`, `payment_last4`, `payment_card_type`, and `expires_at` (`MM/YYYY`). An empty array means no saved cards. The app sends the returned Pine `payment_id` to the charge endpoint; it does not send a raw Stripe PaymentMethod ID.

## 2. Add a card when needed

Call authenticated `POST /customer/home/payment/add`. The handler returns a Stripe Checkout setup URL directly (the HTTP response is serialized as a JSON string). Open it using the platform browser/Stripe Checkout flow. Stripe returns through `/customer/home/payment/add/success` or `/failed`; on return, refresh `/cards` and let the customer select the newly saved card. The success callback is not proof that a particular job was paid; card setup and job payment are separate actions.

## 3. Confirm selected card and pay this offer

Call authenticated `POST /customer/home/payment/{payment_id}/{offer_id}` with no JSON body, replacing both path values with the selected saved-card ID and the exact offer ID. On success the backend charges the saved method, creates the job/payment records, calls the agent webhook, and creates customer and merchant notifications. The current success body is a response message, not a job detail object.

The backend validates that the card and offer belong to this customer and that the offering agent is hired. On declined payment the offer remains available. Successful submissions are protected by an idempotency key/short lock and the offer is consumed after the backend records the job and payment.

## Error and recovery behavior

Display server `detail` messages in a user-friendly way and preserve the offer context for retry when the payment was declined. If the server says the offer was already processed, do not submit another payment; refresh activity and look for the resulting job. If a charge succeeds but a later database/webhook step fails, the full flow is not transactional and there is no durable reconciliation/outbox worker in this checkout. The client cannot safely infer success from a network timeout alone; refresh activity and provide a support/recovery path rather than repeatedly charging.

The Stripe charge, database commit, agent callback, and notifications are separate operations. This is a documented backend limitation, not a mobile retry policy the client can repair.
