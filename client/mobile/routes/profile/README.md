# Profile and settings

There is no mounted customer profile REST or GraphQL route in this checkout. The profile route modules and schemas are placeholders. Do not call a guessed `/customer/profile` endpoint or assume account details can be read/edited from the mobile app.

Authentication currently provides signup, login, verification, and verification-code resend. There is no mounted logout, password reset, profile edit, account deletion, or saved-card removal route documented by the customer API. Add each screen only after the server contract is implemented and registered.
