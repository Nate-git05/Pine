# Server configuration and adapters

`configuration.py` loads required settings from the process environment and `server/.env`. Keep credentials out of source control. `database.py` wraps async Postgres sessions, Redis cache operations, and Qdrant vector operations. `apis.py` holds shared Twilio/OpenAI/Stripe factories and in-process event queues.

This pass fixed awaited Redis list commands, integer conversion for the Redis port at startup, vector collection initialization when an existing collection is present, vector payload attachment during upsert, and point ID extraction during deletion. The notification and incoming-job event wrappers remain separate and each now routes events through customer-keyed queues. `VectorDatabase` defaults its collection name to `agents` so the app startup constructor is valid.

Check collection vector dimensions against the configured embedding model. The current startup defaults to 1024 dimensions. Database adapters have not been exercised against live services in this pass.
