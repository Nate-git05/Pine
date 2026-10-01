# Notifications

## Live notifications

The customer notification stream is authenticated SSE:

`GET /customer/notifications/events`

Events contain `notification_id`, `notification_header`, `notification_message`, and `notification_type`. Use an SSE client that can set `Authorization: Bearer <customer_session_token>`. The stream has a separate queue from incoming job offers.

## Unread notification list

Send an authenticated GraphQL POST to `/customer/notifications` with a query such as:

```graphql
query {
  customerNotifications(limit: 5) {
    statusCode
    response
    cursor
    lastNotificationIdSeen
    returnedNotifications {
      notiId
      notiHeader
      notiMessage
      notiType
      notificationDate
    }
  }
}
```

The list contains unread notifications, newest first. The server caps the page size at 50. For the next page, send the returned `lastNotificationIdSeen` timestamp back as the top-level `last_seen` field and set top-level `cursor` to `true` in the GraphQL HTTP JSON body, alongside the `query`:

```json
{
  "query":"query { customerNotifications(limit: 5) { statusCode cursor lastNotificationIdSeen returnedNotifications { notiId notiHeader notiMessage notiType notificationDate } } }",
  "cursor":true,
  "last_seen":"<lastNotificationIdSeen timestamp>"
}
```

## Read and clear

- `GET /customer/notifications/{notification_id}` retrieves one notification and marks it read. The response includes header, message, type, and a formatted date; the ID is used to select the record, not returned in the response.
- `PATCH /customer/notifications/clear` marks **all unread notifications** for the customer as read. It does not accept a list of IDs and does not clear only the currently displayed page.

SSE has no guaranteed replay after disconnect, so use the GraphQL unread list to reload inbox state rather than relying on the event stream as durable history.
