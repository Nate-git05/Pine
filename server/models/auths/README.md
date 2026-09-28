# Merchant API authentication model

Merchant API signatures use the merchant webhook secret with HMAC-SHA256 and are compared as hex strings. The callback routes also check that the API key's merchant owns the agent associated with the referenced job.
