# Customer webhook API handoff

`job_webhook.py` defines the shared router; the client and request webhook modules attach additional routes to it and must be imported before router registration. The offer route caches the pending offer and publishes it to the separate `IncomingJobsEvents` channel; after customer approval and payment, Pine creates the job and forwards it to the agent. Completion/request callbacks use the merchant API key and signature and publish status updates to `NotificationEvents`.

This pass aligns pending-offer cache writes and reads, fixes signature and merchant API session handling, confirms that callback jobs belong to the signing merchant, and corrects request fields and notification IDs.

Each incoming customer job offer now receives a Pine-generated `offer_id`. The SSE event includes that ID, and the customer payment endpoint is `POST /customer/home/payment/{payment_id}/{offer_id}`. The frontend should retain the offer ID from the SSE event and submit it with the chosen saved payment ID. Offers are cached independently for 15 minutes, so concurrent offers from the same agent do not collide.

The incoming job and notification channels are separate, with events routed by customer ID. The queues are process-local and are not a cross-worker message broker. Verify webhook signatures, replay protection, and delivery retries before production.
