# Customer webhook API handoff

`job_webhook.py` defines the shared router; the client and request webhook modules attach additional routes to it and must be imported before router registration. This pass fixed the client webhook HMAC byte encoding/comparison, stored a JSON-compatible event payload, awaited request notification signaling, and repaired queue reads for client SSE.

The incoming event queues are process-local and are not a cross-worker message broker. Verify webhook signatures, replay protection, and delivery retries before production.
