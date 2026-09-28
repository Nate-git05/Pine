# Customer notification delivery

`notifications_sse.py` streams customer notification queue items and awaits the event signal. Queue reads now use `Queue.empty()` and the event wrappers clear their signal after the last queued item is removed. Events are process-local; concurrent SSE consumers can consume another user's item, and multiple app workers do not share the queue. Use shared pub/sub fanout before production.
