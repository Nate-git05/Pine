# Server configuration and adapters

`configuration.py` loads required settings from the process environment and `server/.env`. It validates required values while importing; keep all credentials out of source control and documentation. The names and runtime sequence are summarized in the [server handoff](../README.md#starting-the-application).

`database.py` wraps three async adapters:

- `RelationalDatabase`: SQLAlchemy async engine/session factory for Postgres.
- `CacheDatabase`: Redis key/value and list access, TTLs, and payment locks.
- `VectorDatabase`: Qdrant client, the `agents` collection, embeddings, payload search, and deletion.

`apis.py` creates Twilio/OpenAI clients and defines separate customer-keyed in-process queues for incoming job offers and notifications. The app creates and closes the database/cache/vector clients and shared HTTP session in its FastAPI lifespan. Agent vectors are initialized with cosine distance and 1024 dimensions; confirm this matches the configured embedding model and existing collection. These adapters have not been verified against live services as part of the documentation pass.
