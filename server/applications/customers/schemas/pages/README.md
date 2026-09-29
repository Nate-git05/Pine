# Customer page schemas

Search request/response models live here alongside activity and profile schemas. The hire response returns both the customer-specific `hired_agent_id` and `hired_agent_name`. Use the ID as the chat route identifier (for example, `/chat/{hired_agent_id}`) and the name for display. Align these models with the customer UI once its source is available.
