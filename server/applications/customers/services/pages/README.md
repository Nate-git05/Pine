# Customer page services

- `search_service.py` maps Qdrant payloads to search results, carries forward seen IDs, and calculates an agent rating from rated completed jobs across hires.
- `home_service.py` queries Stripe for card metadata, creates off-session USD PaymentIntents, writes active job/payment history rows, and resolves the agent endpoint from a customer-owned hire.
- `activity_service.py` builds GraphQL list objects from requests/jobs/payments and retrieves agent/merchant signing information when a customer answers an agent request.

Route handlers still control business sequencing and commit points. Payment and job history, for example, are committed separately before job dispatch; see [`server/README.md`](../../../../README.md#3-job-offer-saved-card-payment-and-dispatch) for failure behavior.
