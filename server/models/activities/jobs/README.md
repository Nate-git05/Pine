# Job and request models

`AgentJob` stores a customer-paid job, its active/done state, integer-cent price, hired-agent/customer references, summary, optional rating, and assigned/completed timestamps. `AgentJobRequest` is an agent-authored request for customer input tied to an existing job; it stores the current summary, question, optional customer response, handled state, and timestamps.

Both use Python-generated UUID primary keys. Ratings remain null until a completed job is rated. Foreign keys point at `hired_agents`, `agent_jobs`, and `customers`; inspect the deployed schema for migration compatibility. Customer access and job lifecycle are in the [server guide](../../../README.md#4-agent-callbacks-activity-and-notifications).
