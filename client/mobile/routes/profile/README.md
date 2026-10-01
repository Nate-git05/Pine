# Profile and settings

All listed customer profile routes require `Authorization: Bearer <customer_session_token>`.

## Profile overview

`GET /profile/page` returns customer name, email, phone number, the last-used saved card (if any), active-agent count, and completed-job count. There is no editable profile route.

## Hired agents

- GraphQL `POST /customer/profile/agents` has `activeHiredAgents` and `firedHiredAgents` queries. Each returns hired-agent ID, name, description, state, and average job rating. Use the returned hire ID when opening the conversation.
- `GET /profile/agents/{hired_agent_id}` returns the hire's image key, price per job, restrictions, abilities, hire time, state, and rating for that customer's jobs.
- `PATCH /profile/agents/fire/{agent_hire_id}` fires an active hire.
- `PATCH /profile/agents/hire/{hired_agent_id_str}` rehires a fired agent.

There is no endpoint for chat history. The app can list active and fired hires after restart, but it cannot restore prior conversation messages from the server.

## Email integrations

- GraphQL `POST /customer/profile/integrations/email` returns a newest-first list with integration ID, provider, email address, and integration time.
- `POST /profile/integrations/email/delete/{integration_id}` permanently removes the customer's integration.
- `POST /profile/oauth2/email/gmail` returns `redirect_url`. Open that authorization URL in an in-app browser or WebView. Google's callback returns to the configured backend redirect route, which stores the Gmail connection and redirects to the backend success or already-connected response.

The Gmail callback currently returns a server response page rather than an app deep link. The mobile UI should handle that return path explicitly before treating the OAuth flow as a native app handoff.

There are no mounted profile-edit, account-delete, server logout, session-refresh, or saved-card-delete routes. `CustomerApi.logoutLocal()` only clears the token from device storage; it does not revoke the server session.
