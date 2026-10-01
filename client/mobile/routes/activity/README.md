# Activity page

The activity surface combines GraphQL lists with REST detail/actions. All routes require the customer Bearer token.

## Lists: GraphQL

POST GraphQL JSON `{ "query": "...", "variables": { "limit": 5 }, "cursor": false, "last_id_seen": null }` to `/customer/activity`. Strawberry's default camel-case field names are used. Query fields take `limit`; pagination state is read by the server from the top-level GraphQL HTTP body, not from GraphQL field arguments. The current query fields are:

- `jobRequests(limit)` for unhandled customer requests. Items include request ID/name/description and creation time. The response has a boolean `cursor` and `lastRequestDate`. The schema currently spells the item timestamp field `rrequestCreatedAt` after camel-casing its Python typo.
- `activeJobs(limit)` for active jobs. Items contain `agentJobId`, `agentJobName`, `agentJobDescription`, and timestamps; the response has a boolean `cursor` and `lastJobDate`.
- `completedJobs(limit)` for completed jobs, with the same item shape and pagination fields.
- `customerJobPayments(limit)` for customer payment history; amounts are returned in dollars.

For the next page, pass the response's `cursor` and matching date (`lastRequestDate`, `lastJobDate`, or `lastPaymentDate`) as top-level `cursor` and `last_id_seen` fields in the next HTTP body. GraphQL errors may be returned in the standard `errors` array. `CustomerApi` implements these top-level cursor fields.

## Job detail and rating

- `GET /customer/activity/jobs/{job_id}` returns job ID/name/description/price, rating, summary, hired-agent ID/name, and active/completed timestamps as applicable. The detail price is in dollars.
- `POST /customer/activity/job/rating/{job_id}` accepts `{"job_rating": 5}`. The server permits rating only a completed job that has not already been rated. A numeric range is not declared in the current route contract, so do not hard-code a range based only on this documentation.

## Request detail and answer

- `GET /customer/activity/jobs/requests/{request_id}` returns request details, current summary, hired-agent ID/name, and requested timestamp.
- `POST /customer/activity/request/answer/{request_id}` accepts `{"customer_response":"Please use the revised dates."}`. The trimmed response is limited to 150 characters. The server sends it to the agent/merchant callback and marks the request handled only after the callback accepts it. The route currently returns no useful response body on success.

There is no REST list endpoint for activity; use GraphQL for the lists above. Confirm the GraphQL schema before shipping because the backend surface has had recent fixes and is not yet represented by generated client types.
