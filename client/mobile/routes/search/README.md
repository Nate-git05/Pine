# Agent discovery

All routes in this page require the customer Bearer token.

## Search agents

`POST /customer/search/agents?limit=10` accepts:

```json
{"search_request":"Help me compare local solar installers","agent_ids_seen":[]}
```

The response contains `returned_agents` (agent ID, name, description, and price) and `agent_seen_lst`. Carry the seen IDs forward when searching/paginating so results can avoid previously returned agents. Search prices are represented in dollars.

## Agent details

`GET /customer/search/agents/{agent_id}` returns `returned_info` with an `agent` object (`agent_id`, `agent_imgicon_key`, `agent_price`, `agent_rating`, `agent_name`, `agent_description`, `agent_skills`) and `merchant` object (`merchant_id`, `merchant_name`, `merchant_imgicon_key`). Prices are dollar values. Image keys are identifiers; no customer image-delivery endpoint is described by this route.

## Hire and fire

- `POST /customer/search/agent/hire/{agent_id}` accepts `{"agent_restrictions":[]}` and returns the new hire ID/name and a response message. Hiring also creates a merchant notification.
- `PATCH /customer/search/agent/fire/{agent_hire_id}` ends the customer-agent hire. The handler does not define a useful response body.

The backend currently has no endpoint to list the customer's hires after app restart. The hire ID is distinct from the public agent ID and may be needed by future chat contracts. Hiring an agent does not create a chat API in this checkout.
