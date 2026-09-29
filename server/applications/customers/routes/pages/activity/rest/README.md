# Customer activity REST routes

These customer-authenticated handlers share `/customer/activity` with the activity GraphQL router. The main [server guide](../../../../../../README.md#4-agent-callbacks-activity-and-notifications) explains how agent callbacks produce activity records.

| Method and path | Behavior |
| --- | --- |
| `GET /jobs/{job_id}` | Return one job owned by the current customer, including details, summary, agent, dollar price, and applicable timestamps. |
| `POST /job/rating/{job_id}` | Set a rating only when the customer's job is complete and not previously rated. The schema does not validate a numeric range. |
| `GET /jobs/requests/{request_id}` | Return one request owned by the customer. |
| `POST /request/answer/{request_id}` | Validate a non-empty response up to 150 characters, post it to the agent's webhook, and mark the request handled after an accepted callback. |

Activity lists are GraphQL fields at `POST /customer/activity` (`jobRequests`, `activeJobs`, `completedJobs`, and `customerJobPayments`), not REST list routes. Response types are in `applications/customers/schemas/pages/activities_schema.py`.

For list pagination, send request-level `cursor` and `last_id_seen` values (or put them in GraphQL `variables`). The auth context validates the request with `CustomerContextRequest`, parses the timestamp, and passes both values to the resolvers. Each list uses its own timestamp field and ordering, fetches one extra row to report whether another page exists, and returns the last timestamp from the current page. Request one paginated activity list at a time because the context cursor is shared across selected fields.
