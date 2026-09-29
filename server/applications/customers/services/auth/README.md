# Customer auth service notes

Shared customer authentication and GraphQL request-context helpers are defined here. REST and GraphQL context authentication both use FastAPI's `HTTPBearer` dependency to extract the Bearer token without tying it to a token-issuing route. They parse its UUID and compare its HMAC hash with the stored session token. The context getter checks expiry, loads the customer, updates `validated_at`, and supplies the database session to GraphQL resolvers.

The GraphQL context getter validates the JSON request body with `CustomerContextRequest.model_validate_json`, so Pydantic casts the `cursor` and `last_id_seen` fields (including values nested under GraphQL `variables`). It falls back to validating query parameters for GET requests, so it does not require a specific HTTP method. It returns `None` for either pagination value when it is absent. Activity resolvers use those values together with their own customer and state filters.
