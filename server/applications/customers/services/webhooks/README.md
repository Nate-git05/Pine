# Webhook service notes

Merchant API authentication obtains an async session through the normal request dependency and validates the `Api-Key` header. Callback ownership is checked by following the job's hired-agent record to its owning merchant. Signatures are hex encoded HMAC-SHA256 values; producers and consumers must sign the exact same serialized JSON body.
