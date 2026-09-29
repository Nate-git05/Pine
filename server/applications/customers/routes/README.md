# Customer routes handoff

`app.py` registers the customer auth, search, home/payment, activity REST and GraphQL, notification REST, GraphQL and SSE, and webhook routers. Notification GraphQL lists unread records with cursor pagination; the REST detail route returns one customer-owned notification and marks it read, while the REST clear route marks all unread notifications read. The notification SSE stream returns new event data. Some webhook route declarations are attached to shared router objects through module imports. Review the generated OpenAPI routes before frontend integration. Profile routes remain incomplete in this checkout.

This branch has no customer UI source to verify the request/response contracts against. Error messages were added to selected failures, but response shapes and endpoint naming still need a client contract review.
