# AI Chatbot — Gemini & Groq

A minimal, clean chatbot that routes messages to either **Google Gemini** or **Groq** based on user selection.

```
general chatbot/
├── backend/
│   ├── main.py            # FastAPI app — all server logic
│   ├── requirements.txt   # Python dependencies
│   └── .env.example       # Template for API keys
└── frontend/
    └── index.html         # Single-file chat UI (HTML + CSS + JS)
```

## Quickstart

### 1. Backend
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up your API keys
cp .env.example .env
# Edit .env and add your real keys

# Start the server
uvicorn main:app --reload
# → http://localhost:8000
```

### 2. Frontend
Just open `frontend/index.html` in your browser — no build step needed.

## API

`POST /chat`
```json
{ "message": "Hello!", "provider": "gemini" }
```
```json
{ "reply": "Hi there!", "provider": "gemini" }
```

## Environment Variables
| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio key |
| `GROQ_API_KEY` | Groq Console key |
