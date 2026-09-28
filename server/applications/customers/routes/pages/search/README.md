# Customer agent search

Search uses OpenAI embeddings and Qdrant payloads; agent details and ratings are read from Postgres. This pass fixed the search path, embedding the user's actual query text, excluding the supplied seen IDs, awaiting payload conversion, resolving agent details through the proper router, and returning a zero rating when no rated jobs exist.

The payload contract must use `agent_description` and include `agent_id`, `agent_price`, and `agent_name`. Confirm existing Qdrant records follow that shape and agree on embedding dimensions.
