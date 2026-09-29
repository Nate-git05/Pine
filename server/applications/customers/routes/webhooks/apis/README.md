# Customer webhook routes

`job_webhook.py` defines `/customer/webhooks`; `client_webhook.py` and `request_webhook.py` add routes to that shared router. `app.py` imports all modules before router registration. The end-to-end flow and failure boundaries are in [`server/README.md`](../../../../../README.md#3-job-offer-saved-card-payment-and-dispatch).

## Caller and auth by endpoint

- `POST /client` is called by an agent/merchant service. It checks a Pine-key HMAC in `Signature`, stores the proposed job in Redis for 900 seconds under a unique offer ID, and emits it to the customer's offer SSE. It is not a mobile API.
- `GET /client/event` is consumed by the authenticated customer and streams each offer with its `offer_id`.
- `PATCH /jobs` and `POST /requests` are callbacks from a merchant service. They require `Api-Key` and `Signature`; the server verifies HMAC and confirms that the API key's merchant owns the agent for the referenced job.

Merchant signatures use HMAC-SHA256 over the Pydantic `model_dump_json()` serialization and compare the hex digest. Producers and Pine must serialize identically. Job completion updates the job, writes customer/merchant notification records, tries to pop a cached completion callback and post it to configured `JOB_WEBHOOK_URL`, then publishes customer SSE. No code in this checkout enqueues that Redis list, so the forwarding step appears to do nothing unless another process seeds it. The request handler creates an unhandled request plus a customer notification and publishes SSE.

After payment, the customer payment route sends the hired agent an `AgentsJobRequest` containing customer/job details and the `agent_restrictions` saved on that customer's hire. The restrictions are the customer's working scope for the agent, and the Pine HMAC signature covers them with the rest of the request. Customer notification event payloads include `noti_type` as well as the notification ID, header, and message.

There is no nonce/replay protection, durable callback outbox, or cross-worker SSE broker. Job/notification writes, callback forwarding, and event publishing can fail independently; inspect persisted state before retrying callbacks. Merchant API credentials are consumed here; this checkout does not mount a merchant app/API for issuing them.
