# Customer authentication schemas

`login.py` and `signup.py` define the customer authentication request and response bodies. `customer_context.py` defines the GraphQL request envelope and its pagination fields. The auth context validates POST JSON with `CustomerContextRequest.model_validate_json`; Pydantic converts `cursor` to a boolean and `last_id_seen` to a `datetime`, whether those values are at the request level or inside GraphQL `variables`.

GET GraphQL requests pass query parameters through `CustomerContextRequest.model_validate`. The schema accepts the JSON-encoded `variables` query parameter and validates its pagination fields the same way.
