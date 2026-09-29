# Customer page schemas

Search request/response models live here alongside activity and profile schemas. `AgentContractResponse` includes the hired-agent name returned by the hire route. Activity GraphQL responses carry a `cursor` boolean and a list-specific last timestamp. For the next page, request-level `cursor` and ISO-8601 `last_id_seen` values are parsed by the GraphQL context and used by the selected resolver. Profile schemas do not imply that profile routes are mounted.

`home_schemas.py` defines the signed `AgentsJobRequest` sent after payment; it includes the customer's saved `agent_restrictions` for the hired agent. Customer notification SSE responses include the notification type together with the notification ID, header, and message.
