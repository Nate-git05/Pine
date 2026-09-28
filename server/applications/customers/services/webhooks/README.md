# Customer webhook services

`webhook_service.py` loads a `MerchantAPI` from the `Api-Key` header, extracts the caller's `Signature`, verifies HMAC-SHA256 against the request's Pydantic `model_dump_json()` serialization, and checks that the merchant owns the agent attached to a job before accepting a callback. It also builds notification text, looks up an agent's webhook, and forwards cached completion data to configured `JOB_WEBHOOK_URL` with a Pine signature.

Initial offer ingress is different: it verifies `Signature` using Pine's server key, then caches/publishes an offer. See the [webhook route guide](../../routes/webhooks/apis/README.md). There is no nonce/replay protection or durable outbox for outbound callbacks.
