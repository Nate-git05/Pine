# Customer routes handoff

`app.py` registers the customer auth, search, home/payment, activity REST and GraphQL, notification SSE, and webhook routers. Startup and shutdown setup lives in `server/lifespan.py`; request-scoped app-state getters live in `server/dependencies.py`. Some route declarations are attached to shared router objects through module imports. Review the generated OpenAPI routes before frontend integration. Profile and notification REST/GraphQL modules are empty or unfinished in this checkout.

This branch has no customer UI source to verify the request/response contracts against. Error messages were added to selected failures, but response shapes and endpoint naming still need a client contract review.
