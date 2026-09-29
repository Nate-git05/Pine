# Server configuration and adapters

`configuration.py` loads required settings from the process environment and `server/.env`. Keep credentials out of source control. `database.py` wraps async Postgres sessions, Redis cache operations, and Qdrant vector operations. `apis.py` holds shared Twilio/OpenAI/Stripe factories and in-process event queues.

This pass fixed awaited Redis list commands, integer conversion for the Redis port at startup, vector collection initialization when an existing collection is present, vector payload attachment during upsert, and point ID extraction during deletion. `NotificationEvents` and `IncomingJobsEvents` remain separate; each uses customer-keyed `asyncio.Event` and `asyncio.Queue` channels. `event_set` chooses the channel from the payload's `customer_id`, queues the complete payload, and sets the event. The SSE handler waits on that customer's event, dequeues one payload, and clears the event after the queue becomes empty. The SSE handlers also check the payload customer ID against the authenticated customer's ID before yielding it. `VectorDatabase` defaults its collection name to `agents` so the app startup constructor is valid.

Check collection vector dimensions against the configured embedding model. The current startup defaults to 1024 dimensions. Database adapters have not been exercised against live services in this pass.
