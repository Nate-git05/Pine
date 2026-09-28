# Notification model

`Notification` stores a customer- or merchant-targeted notification with header/message, type, unread/read state, creation time, and optional read time. Producers persist these rows before attempting live SSE publication. The customer stream is live-only: no mounted history/list/read API currently exposes stored notifications.

The notification producer/consumer flow and process-local SSE limitation are described in the [server guide](../../README.md#4-agent-callbacks-activity-and-notifications). Check existing enum/database values before migration or deployment.
