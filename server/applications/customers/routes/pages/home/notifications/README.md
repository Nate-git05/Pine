# Customer notification delivery

`NotificationEvents` is dedicated to notification updates; `IncomingJobsEvents` is separate for proposed agent jobs. Each manager routes its own events to customer-keyed queues, and the SSE handlers wait on the current customer's queue. Events are process-local; multiple app workers do not share them. Use shared pub/sub fanout before production.
