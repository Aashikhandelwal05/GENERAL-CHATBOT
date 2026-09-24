# OVERVIEW — AI General Chatbot

## What Is This Project?

This is a simple chatbot web application that lets you type a message and get a reply from an AI model. The key feature is that you can switch between two different AI providers — **Google Gemini** and **Groq** — without changing any code. You just pick one from a dropdown and start chatting.

Under the hood, a Python backend receives your message, sends it to the chosen AI provider's API, and returns the reply to the frontend. The frontend is a clean, browser-based interface built with Streamlit.

---

## Who Is It For?

This project is aimed at:

- **Developers learning how to build AI-powered apps** — it shows a clean, minimal pattern for connecting a Python backend to multiple LLM APIs.
- **Interns or students** who want a working chatbot they can run locally and experiment with.
- **Anyone who wants to compare responses from different AI models** by switching providers mid-conversation.

There is no login, no database, and no deployment complexity. You run two commands, open your browser, and it works.

---

## What It Does — Step by Step (User's View)

1. **Open the app** in your browser at `http://localhost:8501`.
2. **Pick an AI provider** from the sidebar dropdown:
   - Google Gemini (gemini-2.5-flash)
   - Groq (openai/gpt-oss-120b)
3. **Type a message** in the chat input box at the bottom and press Enter.
4. The app sends your message to the backend, which calls the selected AI provider.
5. The **AI's reply appears** in the chat window within a few seconds, with a small label showing which provider answered.
6. You can keep chatting — the conversation history stays on screen for the session.
7. You can **switch providers at any time** using the dropdown. The next message will go to the newly selected provider.
8. Click **Clear Chat** in the sidebar to wipe the conversation and start fresh.

---

## Why the Provider-Switching Approach?

Different AI models have different strengths. Some are faster, some are more accurate on certain topics, and some are cheaper to use. Building a chatbot that is locked to one provider means:

- You cannot compare results easily.
- If that provider goes down or changes pricing, you are stuck.
- You cannot upgrade to a better model without rewriting the integration.

This project solves that by keeping each provider's logic in its own separate function in the backend (`call_gemini`, `call_groq`). The `/chat` endpoint just looks at the `provider` field in the request and calls the right function. Adding a new provider in the future means writing one new function — nothing else changes.

This pattern is known as the **Strategy Pattern**: the caller decides which strategy (provider) to use, and the backend executes it. It keeps the code clean and easy to extend.
