# Job payment flow

This is a customer-app flow launched by tapping the job offer card in an agent conversation. Preserve the `offer_id` from the incoming job-offer SSE event for the entire flow.

## 1. Load saved cards

Call authenticated `GET /customer/home/cards`. A successful response has a `payments_lst` array. Each item includes Pine's `payment_id`, `payment_last4`, `payment_card_type`, and `expires_at` (`MM/YYYY`). An empty array means no saved cards. The app sends the returned Pine `payment_id` to the charge endpoint; it does not send a raw Stripe PaymentMethod ID.

## 2. Add a card when needed

Call authenticated `POST /customer/home/payment/add`. The handler returns a Stripe Checkout setup URL directly (the HTTP response is serialized as a JSON string). Open it using the platform browser/Stripe Checkout flow. Stripe returns through `/customer/home/payment/add/success` or `/failed`; on return, refresh `/cards` and let the customer select the newly saved card. The success callback is not proof that a particular job was paid; card setup and job payment are separate actions.

## 3. Confirm selected card and pay this offer

Call authenticated `POST /customer/home/payment/{payment_id}/{agent_id}/{offer_id}` with no JSON body. Use the Pine saved-card ID from `/cards`, the hired-agent ID from the offer event, and that event's exact offer ID. The backend creates or reuses one PaymentIntent for the offer and confirms it while the customer is present. The response status is `succeeded`, `requires_action`, or `processing`.

When status is `requires_action`, pass `client_secret` to Stripe React Native's `handleNextAction`. If that succeeds, call authenticated `POST /customer/home/payment/confirm/{payment_intent_id}`. Pine retrieves the PaymentIntent itself, verifies it belongs to the signed-in customer, and finalizes the job only after Stripe reports `succeeded`. The `payment_intent.succeeded` webhook performs the same recovery if the app closes or loses its response.

Before the customer confirms, show the amount and selected card (brand and last four digits) so they can verify which method will be charged. After they confirm, set a processing state and disable the Pay button and card selection until the request finishes. This prevents accidental duplicate taps in the app; it is a frontend interaction rule, not a backend payment lock.

The backend validates that the saved card belongs to this customer, the offer belongs to this customer and selected hired agent, and the agent is active. The Stripe idempotency key is stable per customer and offer, independent of the selected card. Pine stores the offer ID and PaymentIntent ID on the payment record with a unique constraint, so a retry resumes the same payment and cannot create another job for that offer. Declined offers remain available; successful offers are removed after Pine records the job and payment.

## Error and recovery behavior

Display server `detail` messages in a user-friendly way and preserve the offer while the response status is `processing`. A retry with the same offer retrieves the same PaymentIntent; it does not issue a second charge. If the server says the offer was already processed, refresh activity and look for the resulting job. Pine's database job/payment commit is atomic. Remote agent delivery remains a separate operation; requests include the stable job ID as an idempotency key, and agent endpoints should deduplicate that key.

Keep `EXPO_PUBLIC_STRIPE_PUBLISHABLE_KEY` in the mobile app environment. The Stripe secret and webhook signing secret stay server-side. Stripe Tax is not currently part of this payment contract.
