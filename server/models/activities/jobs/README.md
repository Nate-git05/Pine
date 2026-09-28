# Job model notes

`AgentJob` and `AgentJobRequest` use generated UUID primary keys. Job ratings are nullable until a completed job is rated, and `AgentJob.customer_id` now references `customers.id` consistently with the user table mapping. Confirm this matches the live database and migrate as needed.
