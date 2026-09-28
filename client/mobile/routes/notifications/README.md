# Notifications

The current customer notification interface is authenticated SSE:

`GET /customer/notifications/events`

Events contain `notification_id`, `notification_header`, and `notification_message`. Use an SSE client that can set `Authorization: Bearer <customer_session_token>`. The stream has a separate queue from incoming job offers.

Notification records are created by server actions, but notification REST/GraphQL list modules are empty/unregistered. There is no unread-count, mark-read, or notification-history endpoint. SSE has no guaranteed replay after disconnect, so this stream alone cannot provide a durable notification inbox.
