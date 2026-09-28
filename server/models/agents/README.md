# Agent models

`Agent` is the merchant-owned catalog/search record: name, description, skills, state, price per job in cents, webhook URL, and image/skill storage keys. Qdrant stores searchable embeddings with a subset of these values in payloads. `HiredAgent` is the customer-specific relationship created on hire; it snapshots display/price fields and stores restrictions and active/fired state.

Both models use Python-generated UUID primary keys. Hired-agent rating defaults to zero; actual public search detail rating is calculated from rated completed jobs. A hire ID is distinct from the public agent ID. The search/hire flow is in the [server guide](../README.md#2-search-and-hire-an-agent). Compare model columns with deployed schema before rollout.
