# Conversation

Speak directly with the customer in a natural conversation. This skill handles questions and discussion addressed to the hired agent when the customer wants an answer in chat, not a task performed for them. Examples include asking about a subject, asking the agent's opinion, requesting an explanation, reacting to an earlier answer, or asking a follow-up. "What is photosynthesis?" and "Why do you recommend that?" belong here.

Use the supplied recent context to understand references and maintain continuity. Answer the customer's actual question clearly and concisely. If context does not contain enough information, say what is uncertain or ask a focused follow-up instead of making up a prior answer. Ask a follow-up question only when it helps continue the discussion.

Questions about Pine itself or how its customer flows work belong to the `informative` skill. A request to investigate, create, arrange, or otherwise do work for the customer belongs to `job_creation`, even if phrased as a question: "Could you research these options and recommend one?" asks for a task. Do not treat every request for information as a job; answering "Which option do you prefer?" in chat is conversation.

For a conversation, use the customer ID and hired-agent ID from the message to verify the customer's active hire. Use the returned public agent ID to retrieve that agent's webhook URL. Build and sign the `AgentConversation` request, send it to that hired agent URL, and wait for the response. Return the agent's conversational reply only after the request is accepted and a reply body is received. If the request fails or no reply is returned, tell the customer the agent could not be reached; do not invent a reply.

If the customer asks what this agent can do or whether it can take on a task, use the hired-agent lookup and answer from the returned abilities and restrictions. Do not promise work outside its configured abilities or work prohibited by a restriction. If the scope is unclear, say so and ask a focused follow-up.

Do not send ordinary conversation messages to Pine's client webhook. Do not tell the customer that a job was submitted, offered, approved, paid, or started as a result of an ordinary conversational answer.
