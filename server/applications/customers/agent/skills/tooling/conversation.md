# Conversation

Speak directly with the customer in a natural conversation. This skill handles questions and discussion addressed to the hired agent when the customer wants an answer in chat, not a task performed for them. Examples include asking about a subject, asking the agent's opinion, requesting an explanation, reacting to an earlier answer, or asking a follow-up. "What is photosynthesis?" and "Why do you recommend that?" belong here.

Use the supplied recent context to understand references and maintain continuity. Answer the customer's actual question clearly and concisely. If context does not contain enough information, say what is uncertain or ask a focused follow-up instead of making up a prior answer. Ask a follow-up question only when it helps continue the discussion.

Questions about Pine itself or how its customer flows work belong to the `informative` skill. A request to investigate, create, arrange, or otherwise do work for the customer belongs to `job_creation`, even if phrased as a question: "Could you research these options and recommend one?" asks for a task. Do not treat every request for information as a job; answering "Which option do you prefer?" in chat is conversation.

The conversation flow sends the customer's message to the hired agent's conversation endpoint and waits for the agent's conversational reply. Return the reply to the customer. Do not tell the customer that a job was submitted, approved, paid, or started as a result of an ordinary conversational answer. Do not claim the hired agent replied unless a reply was received.
