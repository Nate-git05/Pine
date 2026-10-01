# Client applications

The customer mobile app belongs in [`mobile/`](mobile/README.md) and is planned as a React Native app. The merchant application belongs in `web/` and is a separate Next.js app. Neither application has source code in this checkout yet; `mobile/` documents the customer-to-server integration contract based on the FastAPI routes that are currently mounted.

Start with the [mobile route index](mobile/README.md) for the customer app. Merchant UI and API integration are outside this document.
