# Customer webhook API handoff

`job_webhook.py` defines the shared router; the client and request webhook modules attach additional routes to it and must be imported before router registration. The offer route caches the pending offer and publishes it to the separate `IncomingJobsEvents` channel; after customer approval and payment, Pine creates the job and forwards it to the agent. Completion/request callbacks use the merchant API key and signature and publish status updates to `NotificationEvents`.

This pass aligns pending-offer cache writes and reads, fixes signature and merchant API session handling, confirms that callback jobs belong to the signing merchant, and corrects request fields and notification IDs.

Each incoming customer job offer now receives a Pine-generated `offer_id`. The SSE event includes that ID, and the customer payment endpoint is `POST /customer/home/payment/{payment_id}/{offer_id}`. The frontend should retain the offer ID from the SSE event and submit it with the chosen saved payment ID. Offers are cached independently for 15 minutes, so concurrent offers from the same agent do not collide.

After payment, Pine sends the hired agent an `AgentsJobRequest` containing the customer ID, job ID, job name and description, plus the `agent_restrictions` saved when the customer hired that agent. This is the customer's working scope for the agent. The request signature covers the full serialized payload, including those restrictions.

The incoming-job and notification channels are separate, with customer-keyed queues inside each channel. `event_set` reads the payload's customer ID to choose a queue, then stores the complete payload and wakes that customer's stream. The incoming-job SSE inner loop checks the queued customer ID against the authenticated customer before sending the offer. The notification SSE uses the same check. These checks sit in the stream loops as a second guard after channel routing. The queues are process-local and are not a cross-worker message broker. Verify webhook signatures, replay protection, and delivery retries before production.
