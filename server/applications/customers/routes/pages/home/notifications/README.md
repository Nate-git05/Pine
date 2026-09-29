# Customer notification delivery

Customer notification records are stored in Postgres. The list and update routes are registered in `app.py`; they share the `/customer/notifications` prefix with the notification SSE endpoint.

## Notification history

- The GraphQL route at `POST` or `GET /customer/notifications` returns unread notifications newest-first. It accepts a `limit` (bounded to 1–50), fetches one extra row to set `cursor`, and returns the timestamp of the last displayed notification. Send `cursor` and `last_seen` with the next request; the auth context also accepts `last_id_seen`.
- `GET /customer/notifications/{notification_id}` returns the matching notification only when it belongs to the signed-in customer. Reading an unread notification changes its state to `read` and sets `read_at`.
- `PATCH /customer/notifications/clear` marks all unread notifications for the signed-in customer as read and sets `read_at`. It does not clear only the current GraphQL page.

## Live events

`NotificationEvents` is separate from `IncomingJobsEvents`. Each manager routes to a queue and `asyncio.Event` keyed by customer ID. Notification producers persist the row before queueing an event containing `customer_id` and `customer_noti` (`noti_id`, `noti_header`, `noti_message`, and `noti_type`). The SSE response sends the ID, header, message, and type. The stream checks the event's customer ID against the authenticated customer before yielding it.

The event is a wake-up signal and the queue holds payloads. The event remains set while that customer's queue has items and is cleared when it becomes empty. Events are process-local; multiple workers do not share them, and a disconnected client cannot replay missed events from SSE. Use a shared broker and durable replay/outbox design before relying on multi-worker delivery.

For the full customer lifecycle and failure boundaries, see the [server guide](../../../../../../README.md#4-agent-callbacks-activity-and-notifications).
