# Customer agent search and hiring

The full place in startup and customer flow is described in [`server/README.md`](../../../../../README.md#2-search-and-hire-an-agent). These routes require a customer Bearer session.

- `POST /customer/search/agents?limit=10` embeds `search_request` with the configured OpenAI model, queries Qdrant's `agents` collection, optionally excludes `agent_ids_seen`, then maps payloads to search results. Payloads must contain `agent_id`, `agent_name`, `agent_description`, and `agent_price`; price is stored in cents and returned divided by 100.
- `GET /customer/search/agents/{agent_id}` loads agent and merchant data from Postgres and derives a rating from rated completed jobs. No ratings returns `0.0`.
- `POST /customer/search/agent/hire/{agent_id}` creates a customer-owned `HiredAgent` row with restrictions and creates a merchant notification record.
- `PATCH /customer/search/agent/fire/{agent_hire_id}` marks the current customer's hire as fired.

The API does not list a customer's hired agents or create chat sessions/messages. Keep agent ID and hired-agent ID distinct: search/hire uses the public agent ID; fire uses the customer-specific hire ID. Check Qdrant payload compatibility and vector dimensions when indexing is implemented or changed.
