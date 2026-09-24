"""
=============================================================
  Chatbot Backend — FastAPI
=============================================================
  Author  : Internship Demo
  Purpose : Expose a single POST /chat endpoint that routes
            a user message to either Google Gemini or Groq,
            then returns the model's reply.

  Principal-Engineer Notes
  ------------------------
  * We keep ONE endpoint and let a "provider" field drive
    the routing logic.  This is the Strategy Pattern: the
    caller tells us which "strategy" (Gemini vs Groq) to
    use; we just run it.
  * All I/O is async (httpx.AsyncClient) so FastAPI can
    serve other requests while we wait for the LLM API.
  * Keys come from environment variables — never hardcoded.
  * CORS is wide-open here (origins=["*"]) because this is a
    demo.  In production you'd restrict it to your domain.
=============================================================
"""

import os
import httpx

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# ── 1. Load .env file so os.getenv() can see GEMINI_API_KEY etc. ──────────────
#    load_dotenv() reads a file called ".env" in the working directory.
#    In production you'd inject env vars at the platform level (Docker, Railway…),
#    but for a local demo .env is fine.
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")

# ── 2. Create the FastAPI app ──────────────────────────────────────────────────
app = FastAPI(
    title="Multi-Provider Chatbot API",
    description="Routes messages to Gemini or Groq based on 'provider' field.",
    version="1.0.0",
)

# ── 3. CORS Middleware ─────────────────────────────────────────────────────────
#    Without this, the browser blocks our frontend from calling the API because
#    they run on different ports (8000 vs file://).  allow_origins=["*"] means
#    ANY origin is allowed — fine for demos, restrictive in prod.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Accept requests from any origin
    allow_credentials=True,
    allow_methods=["*"],        # GET, POST, OPTIONS, etc.
    allow_headers=["*"],        # Accept any request header
)

# ── 4. Request / Response Schemas (Pydantic) ───────────────────────────────────
#    Pydantic validates incoming JSON automatically.  If the client sends a
#    wrong type FastAPI returns a 422 before your code even runs.

class ChatRequest(BaseModel):
    message: str                        # The user's text
    provider: str = "gemini"            # "gemini" or "groq"

class ChatResponse(BaseModel):
    reply: str                          # The model's text response
    provider: str                       # Echo back which provider answered


# ── 5. Provider helper functions ───────────────────────────────────────────────
#    Each function is responsible for EXACTLY one provider.  This keeps the main
#    endpoint clean and makes it trivial to add a third provider later.

async def call_gemini(message: str) -> str:
    """
    Call Google Gemini generateContent API.

    Endpoint pattern:
        POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}

    Payload structure (simplified):
        { "contents": [ { "parts": [ { "text": "..." } ] } ] }

    Returns the model's text as a plain string.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set.")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    )

    payload = {
        "contents": [
            {
                "parts": [{"text": message}]
            }
        ]
    }

    # httpx.AsyncClient is the async version of the popular requests library.
    # We use `async with` so the connection is properly closed after the call.
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, json=payload)

    # If Gemini returns 4xx/5xx, surface a meaningful error to the caller.
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Gemini API error: {response.text}",
        )

    data = response.json()

    # Navigate the nested Gemini response structure to get the text.
    # Structure: data["candidates"][0]["content"]["parts"][0]["text"]
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unexpected Gemini response structure: {exc}",
        )


async def call_groq(message: str) -> str:
    """
    Call Groq's chat completions API (OpenAI-compatible endpoint).

    Groq uses the same request/response format as OpenAI, so if you've
    used the OpenAI SDK before this will look very familiar.

    Endpoint:
        POST https://api.groq.com/openai/v1/chat/completions

    Payload (OpenAI chat format):
        { "model": "...", "messages": [ {"role": "user", "content": "..."} ] }
    """
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not set.")

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "openai/gpt-oss-120b",   # Model hosted on Groq's infrastructure
        "messages": [
            {"role": "user", "content": message}
        ],
        "temperature": 0.7,               # Controls creativity (0 = deterministic, 1 = creative)
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Groq API error: {response.text}",
        )

    data = response.json()

    # OpenAI/Groq response structure: data["choices"][0]["message"]["content"]
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unexpected Groq response structure: {exc}",
        )


# ── 6. The main /chat endpoint ─────────────────────────────────────────────────
#    This is where the Strategy Pattern plays out: we look at `provider` and
#    dispatch to the correct helper.  The endpoint itself stays clean — no
#    vendor-specific logic lives here.

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Route a user message to the selected LLM provider.

    Body:
        { "message": "Hello!", "provider": "gemini" | "groq" }

    Returns:
        { "reply": "...", "provider": "gemini" | "groq" }
    """

    # ── Provider-switching logic ───────────────────────────────────────────────
    #    A simple if/elif block is perfectly readable for two providers.
    #    If you add more (OpenAI, Anthropic, Cohere…), consider replacing
    #    this with a dict of callables: PROVIDERS = {"gemini": call_gemini, ...}
    # ──────────────────────────────────────────────────────────────────────────

    if request.provider == "gemini":
        reply = await call_gemini(request.message)

    elif request.provider == "groq":
        reply = await call_groq(request.message)

    else:
        # Unknown provider — return 400 Bad Request so the client knows it
        # sent something wrong (not a server fault → not 500).
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider '{request.provider}'. Use 'gemini' or 'groq'.",
        )

    return ChatResponse(reply=reply, provider=request.provider)


# ── 7. Health-check endpoint ───────────────────────────────────────────────────
#    Always add a /health endpoint.  Load balancers, Docker HEALTHCHECK, and
#    monitoring systems all ping this to know if the app is alive.

@app.get("/health")
async def health():
    return {"status": "ok"}


# ── 8. Dev entry point ─────────────────────────────────────────────────────────
#    `uvicorn main:app --reload` is the standard way to run FastAPI locally.
#    The `if __name__ == "__main__"` block lets you also do `python main.py`.

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
