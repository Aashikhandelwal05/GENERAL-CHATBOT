# AI General Chatbot — Gemini & Groq

A simple chatbot that routes messages to either **Google Gemini** or **Groq** based on user selection.

## Project Structure

```
general chatbot/
├── backend/
│   ├── main.py            # FastAPI backend — /chat endpoint
│   ├── requirements.txt   # Python dependencies
│   └── .env               # API keys (never commit this)
└── streamlit_app.py       # Streamlit frontend
```

## Setup

### 1. Add your API keys

Edit `backend/.env`:

```
GEMINI_API_KEY=your-gemini-key-here
GROQ_API_KEY=your-groq-key-here
```

### 2. Install dependencies

```bash
cd backend
python -m pip install -r requirements.txt
```

## Running the App

You need **two terminals** running at the same time.

**Terminal 1 — Start the backend:**
```bash
cd backend
python -m uvicorn main:app --reload
```
Backend runs at: http://localhost:8000

**Terminal 2 — Start the frontend:**
```bash
cd "general chatbot"
python -m streamlit run streamlit_app.py
```
Frontend runs at: http://localhost:8501

## Providers

| Provider | Model |
|---|---|
| Google Gemini | gemini-2.5-flash |
| Groq | openai/gpt-oss-120b |

## API

`POST /chat`
```json
{ "message": "Hello!", "provider": "gemini" }
```
Response:
```json
{ "reply": "Hi there!", "provider": "gemini" }
```

`GET /health` — returns `{ "status": "ok" }`
