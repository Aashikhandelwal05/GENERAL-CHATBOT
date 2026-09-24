import streamlit as st
import requests

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Chatbot", page_icon="🤖", layout="centered")

# ── Backend URL ───────────────────────────────────────────────────────────────
API_URL = "http://localhost:8000/chat"

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")
    provider = st.selectbox(
        "AI Provider",
        options=["gemini", "openai", "groq"],
        format_func=lambda x: {
            "gemini": "✨ Google Gemini (gemini-2.5-flash)",
            "openai": "🧠 OpenAI (gpt-4o-mini)",
            "groq":   "⚡ Groq (gpt-oss-120b)",
        }[x],
    )
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── Title ─────────────────────────────────────────────────────────────────────
st.title("🤖 AI Chatbot")
st.caption("Powered by Google Gemini, OpenAI & Groq")
st.divider()

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Render chat history ───────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("provider"):
            labels = {"gemini": "✨ Gemini", "openai": "🧠 OpenAI", "groq": "⚡ Groq"}
            st.caption(f"Answered by **{labels.get(msg['provider'], msg['provider'])}**")

# ── Empty state ───────────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.info("👈 Pick a provider in the sidebar, then start chatting below!")

# ── Chat input ────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask anything…"):

    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call backend and show reply
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                response = requests.post(
                    API_URL,
                    json={"message": prompt, "provider": provider},
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()
                reply = data["reply"]
                answered_by = data.get("provider", provider)

            except requests.exceptions.ConnectionError:
                reply = "⚠️ Cannot connect to the backend. Make sure uvicorn is running on port 8000."
                answered_by = None

            except requests.exceptions.Timeout:
                reply = "⚠️ Request timed out. The AI provider may be slow — try again."
                answered_by = None

            except requests.exceptions.HTTPError as e:
                detail = response.json().get("detail", str(e))
                reply = f"⚠️ Backend error: {detail}"
                answered_by = None

        st.markdown(reply)
        if answered_by:
            labels = {"gemini": "✨ Gemini", "openai": "🧠 OpenAI", "groq": "⚡ Groq"}
            st.caption(f"Answered by **{labels.get(answered_by, answered_by)}**")

    st.session_state.messages.append({
        "role": "assistant",
        "content": reply,
        "provider": answered_by,
    })
