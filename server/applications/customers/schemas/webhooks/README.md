# Webhook payload contracts

The incoming client-offer payload requires customer and agent identifiers, names, a description, and a positive `job_price` in cents. The customer-facing offer schema includes the agent ID needed to match the offer to a hired agent before payment. Completion and request callback payload fields are required so malformed callbacks fail at the API boundary.
