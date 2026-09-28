# Customer webhook payload contracts

`webhook_schema.py` defines three agent/merchant-originated payloads: a proposed client job (`customer_id`, `agent_id`, names/descriptions, positive integer `job_price` in cents), a job completion (`job_id`, `job_action_summary`), and a job request (`job_id`, request name/description, current summary). Pine's generated offer SSE adds a unique `offer_id` and converts its display price to dollars.

These bodies are signed as their Pydantic `model_dump_json()` serialization. Callback merchant API credentials and signature validation are in `services/webhooks/webhook_service.py`; initial offer ingress instead validates Pine's server key. See the [webhook route guide](../../routes/webhooks/apis/README.md) for call direction and effects.
