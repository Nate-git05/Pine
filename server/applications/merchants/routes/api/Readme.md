# Merchant API routes

There are no registered merchant API routes in this checkout. Customer webhook callbacks accept merchant `Api-Key` and `Signature` headers, but the merchant route modules that would provision/use those credentials are not implemented or mounted by `server/app.py`.

See the [server scope and callback guide](../../../../README.md#scope-and-current-completeness). Treat the customer webhook routes as an integration boundary, not as a complete merchant backend.
