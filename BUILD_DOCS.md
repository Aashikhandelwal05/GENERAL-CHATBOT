# BUILD DOCS — AI General Chatbot

## Tech Stack

### Backend
| Tool | Version | Purpose |
|---|---|---|
| Python | 3.14.7 | Runtime language |
| FastAPI | 0.141.1 | Web framework for the API server |
| Uvicorn | 0.53.0 | ASGI server that runs FastAPI |
| httpx | 0.28.1 | Async HTTP client for calling AI provider APIs |
| python-dotenv | 1.2.3 | Loads API keys from the `.env` file |
| Pydantic | 2.13.5 | Request/response validation (built into FastAPI) |
| Starlette | 1.7.0 | ASGI toolkit underlying FastAPI |

### Frontend
| Tool | Version | Purpose |
|---|---|---|
| Streamlit | 1.64.0 | Python-based web UI framework |
| requests | 2.34.2 | HTTP client for calling the FastAPI backend |

### External AI APIs
| Provider | Model | API Endpoint |
|---|---|---|
| Google Gemini | gemini-2.5-flash | `generativelanguage.googleapis.com/v1beta` |
| Groq | openai/gpt-oss-120b | `api.groq.com/openai/v1/chat/completions` |

---

## Project Structure

```
general chatbot/
├── backend/
│   ├── main.py            # FastAPI app — all API logic lives here
│   ├── requirements.txt   # Python dependencies
│   └── .env               # API keys (gitignored, never committed)
└── streamlit_app.py       # Streamlit frontend — chat UI
```

---

## How This Was Built

### Step 1 — Backend (`backend/main.py`)

The backend is a single FastAPI application with two endpoints:

**`POST /chat`** — the main endpoint. It receives a JSON body:
```json
{ "message": "your question here", "provider": "gemini" }
```
It routes the message to the correct AI provider and returns:
```json
{ "reply": "AI response here", "provider": "gemini" }
```

**`GET /health`** — returns `{ "status": "ok" }`. Used to check if the server is running.

The routing works through a dictionary called `PROVIDERS`:
```python
PROVIDERS = {
    "gemini": call_gemini,
    "groq":   call_groq,
}
```
When a request comes in, the code looks up the provider name in this dictionary and calls the matching function. Each function (`call_gemini`, `call_groq`) handles one provider: it builds the correct HTTP request, sends it using `httpx.AsyncClient`, and parses the response.

CORS middleware is added so that any frontend (running on a different port) can call the API without being blocked by the browser.

API keys are loaded from a `.env` file using `python-dotenv`. They are never hardcoded.

### Step 2 — Gemini Integration

Gemini uses a REST API at:
```
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}
```
The payload format is:
```json
{ "contents": [{ "parts": [{ "text": "message here" }] }] }
```
The reply is extracted from:
```
response["candidates"][0]["content"]["parts"][0]["text"]
```

Note: `gemini-1.5-flash` was the original model but returned a 404 — it has been deprecated on the v1beta API. It was updated to `gemini-2.5-flash`, which is the current working equivalent.

### Step 3 — Groq Integration

Groq uses an OpenAI-compatible endpoint:
```
POST https://api.groq.com/openai/v1/chat/completions
```
Authentication is via a Bearer token in the `Authorization` header. The payload and response structure are identical to the OpenAI chat completions format:
```json
{ "model": "openai/gpt-oss-120b", "messages": [{ "role": "user", "content": "message" }] }
```
The reply is extracted from:
```
response["choices"][0]["message"]["content"]
```

### Step 4 — Frontend (`streamlit_app.py`)

The frontend is a Streamlit app. Streamlit lets you build web UIs entirely in Python — no HTML, CSS, or JavaScript required.

Key components:
- `st.sidebar` — contains the provider dropdown and Clear Chat button.
- `st.chat_message` — renders chat bubbles for user and assistant messages.
- `st.chat_input` — sticky input bar at the bottom of the page.
- `st.session_state.messages` — a list that stores the full conversation for the current browser session. Streamlit reruns the script on every interaction, so session state is how data persists.

When the user sends a message, the frontend makes a synchronous `POST` request to `http://localhost:8000/chat` using the `requests` library, then displays the reply.

Error handling covers three cases: backend not running (ConnectionError), slow response (Timeout), and API errors (HTTPError).

---

## Environment Variables

These must be set in `backend/.env` before running:

| Variable | Where to get it | Required |
|---|---|---|
| `GEMINI_API_KEY` | Google AI Studio — aistudio.google.com | Yes, for Gemini |
| `GROQ_API_KEY` | Groq Console — console.groq.com | Yes, for Groq |

Example `.env` file:
```
GEMINI_API_KEY=your-gemini-key-here
GROQ_API_KEY=your-groq-key-here
```

---

## How to Run

You need two terminals open at the same time.

### Terminal 1 — Start the Backend

```powershell
cd "F:\general chatbot\backend"
python -m uvicorn main:app --reload
```

The server starts at `http://localhost:8000`.  
You can view the auto-generated API docs at `http://localhost:8000/docs`.

The `--reload` flag makes the server automatically restart when you edit `main.py`.

### Terminal 2 — Start the Frontend

```powershell
cd "F:\general chatbot"
python -m streamlit run streamlit_app.py
```

The app opens in your browser at `http://localhost:8501`.

> **Note:** Use `python -m uvicorn` and `python -m streamlit` instead of `uvicorn` and `streamlit` directly. This is required when Python's Scripts folder is not added to the system PATH (common on Windows).

---

## Installing Dependencies

```powershell
cd "F:\general chatbot\backend"
python -m pip install -r requirements.txt
```

Contents of `requirements.txt`:
```
fastapi
uvicorn[standard]
httpx
python-dotenv
streamlit
requests
```
