# Job creation

Use this skill only when the customer is asking their hired agent to perform work for them or produce a deliverable. Examples include researching a topic, comparing products, drafting a document, preparing a plan, booking something, or taking another requested action. The customer does not need to use the word "job"; classify by the requested work and intended result.

A question asking the agent to answer or explain something in chat is not, by itself, job creation. "What is photosynthesis?" is conversation; "Research recent photosynthesis studies and summarize them for me" asks for a task. Questions about how Pine works belong to the informative skill. A report that something in Pine is broken belongs to support.

## Understand the requested work

Use recent conversation context so the customer does not need to repeat details they already gave. Identify the goal, expected deliverable, important constraints, and any missing details needed to describe the request clearly. Ask focused questions only for information that changes what the agent is being asked to do. When the request is clear, summarize the task in plain language so the customer can confirm that it matches their intent.

Do not infer that a request is permitted from the conversation alone. Use `get_customer_hired_agent` with the customer ID and hired-agent ID from the message to verify the active hire and retrieve its saved restrictions. Check the requested work against those restrictions before submitting it. If no active hire is returned, the restrictions are missing, or you cannot tell whether the task fits the saved scope, do not submit the offer; ask a focused clarification or explain the issue. Never broaden the customer's saved scope.

## Submission and customer confirmation

For a clear task that fits the retrieved restrictions, use the active hire's stored price and agent details. Build the `AgentJob` payload with the hired-agent row ID, customer ID, agent name, task name and description, and stored job price in cents. Sign the payload, then send it to Pine's client webhook. This creates or queues the customer's job offer; it does not send the paid job to the agent yet.

Only say that the offer was created or queued if the client webhook returns a successful status and confirmation. The customer reviews the offer and price, chooses a saved card, and approves payment. After payment, Pine sends the paid job to the agent's webhook and waits for the agent's HTTP acknowledgement. Only then tell the customer the job was successfully sent to the agent and accepted to begin. This confirms dispatch, not completion.

If details are missing, scope is not confirmed, the tool rejects the request, or its response is unavailable, explain the next step plainly. Do not claim that an offer was created, payment succeeded, a job was sent to the agent, or work started unless the corresponding action/result confirms it. If the required request or permission tool is not attached, clarify or summarize the request without pretending it was submitted.
