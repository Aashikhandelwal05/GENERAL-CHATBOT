import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")

app = FastAPI(title="Multi-Provider Chatbot API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas 
class ChatRequest(BaseModel):
    message: str
    provider: str = "gemini"   # "openai" | "gemini" | "groq"

class ChatResponse(BaseModel):
    reply: str
    provider: str


# ── Provider helpers 


async def call_gemini(message: str) -> str:
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set.")


    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [{"parts": [{"text": message}]}]
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, json=payload)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Gemini error: {response.text}",
        )

    try:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise HTTPException(status_code=502, detail=f"Unexpected Gemini response: {e}")


async def call_groq(message: str) -> str:
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not set.")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [{"role": "user", "content": message}],
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Groq error: {response.text}",
        )

    try:
        return response.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise HTTPException(status_code=502, detail=f"Unexpected Groq response: {e}")


# ── Main endpoint 

PROVIDERS = {
    "gemini": call_gemini,
    "groq":   call_groq,
}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    handler = PROVIDERS.get(request.provider)
    if not handler:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider '{request.provider}'. Choose from: {list(PROVIDERS)}",
        )
    reply = await handler(request.message)
    return ChatResponse(reply=reply, provider=request.provider)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
