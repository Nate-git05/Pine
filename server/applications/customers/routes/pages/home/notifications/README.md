# Customer notification delivery

The only mounted customer notification read surface is authenticated `GET /customer/notifications/events`, implemented in `notifications_sse.py`. Producers persist a `Notification` row and then publish an event containing its ID, header, and message. Producers include job payment/dispatch, agent job completion, and agent requests.

`NotificationEvents` is separate from `IncomingJobsEvents`; both are process-local `asyncio.Event`/`Queue` managers keyed by customer ID. SSE waits for the current customer's queue and sends the next item. It does not replay stored rows after reconnect, and one process cannot share events with other workers. Notification REST and GraphQL modules are placeholders and are not mounted, so there is no inbox/history, unread count, or mark-read route.

For the complete lifecycle and operational limits, see [`server/README.md`](../../../../../../README.md#4-agent-callbacks-activity-and-notifications).
