# Customer activity routes

The activity REST handlers return one job/request or accept a rating/request response. Activity lists are GraphQL at `POST /customer/activity`.

## REST endpoints

- `GET /customer/activity/jobs/{job_id}` returns a customer-owned job.
- `POST /customer/activity/job/rating/{job_id}` accepts a rating only for a completed, unrated job.
- `GET /customer/activity/jobs/requests/{request_id}` returns a customer-owned agent request.
- `POST /customer/activity/request/answer/{request_id}` sends a non-empty response (up to 150 characters) to the hired agent, then marks the request handled after the callback succeeds.

## GraphQL list pagination

The query fields are `jobRequests(limit)`, `activeJobs(limit)`, `completedJobs(limit)`, and `customerJobPayments(limit)`. Send request-level `cursor` and `last_id_seen` values with the GraphQL request JSON. `cursor` is a boolean; `last_id_seen` is the prior response's list-specific timestamp encoded as ISO-8601. The context getter casts that value to a `datetime`. Each resolver combines it with customer and state predicates and the appropriate time condition; it fetches one extra row to set the returned `cursor` only when more results exist.

The request-level cursor/time pair is shared by selected fields, so request one paginated list at a time. The response timestamp fields are `lastRequestDate`, `lastJobDate`, and `lastPaymentDate` after Strawberry camel-casing.
