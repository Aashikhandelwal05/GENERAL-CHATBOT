"""
=============================================================
  Chatbot Frontend — Streamlit
=============================================================
  Talks to the FastAPI backend at http://localhost:8000/chat
  Run with:  streamlit run frontend/app.py
             (from the project root)
=============================================================
"""

import streamlit as st
import requests

# ── Page config ───────────────────────────────────────────────────────────────
#   Must be the FIRST Streamlit call in the script.
#   layout="centered" keeps the chat column readable (not stretched full-width).
st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="centered",
)

# ── Custom CSS — inject dark glassmorphism style ──────────────────────────────
#   Streamlit lets you inject raw CSS via st.markdown(unsafe_allow_html=True).
#   We target Streamlit's own internal class names to restyle the chat bubbles.
st.markdown("""
<style>
/* Google Font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark gradient background */
.stApp {
    background: linear-gradient(135deg, #0d0f14 0%, #161b27 100%);
}

/* Hide Streamlit's default toolbar/header clutter */
#MainMenu, footer, header { visibility: hidden; }

/* Style the chat input box */
.stChatInputContainer {
    border-top: 1px solid rgba(255,255,255,0.07);
    padding-top: 12px;
}

/* User message bubble */
[data-testid="stChatMessageContent"] {
    border-radius: 16px;
    padding: 2px 4px;
}

/* Provider badge pill in sidebar */
.provider-badge {
    display: inline-block;
    background: rgba(99,102,241,0.2);
    border: 1px solid rgba(99,102,241,0.4);
    color: #a5b4fc;
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    margin-top: 6px;
}
</style>
""", unsafe_allow_html=True)


# ── Backend URL ───────────────────────────────────────────────────────────────
#   Change this if your FastAPI server runs on a different host/port.
API_URL = "http://localhost:8000/chat"


# ── Sidebar — provider selector + info ───────────────────────────────────────
#   st.sidebar keeps controls out of the main chat flow — clean UX.
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.markdown("---")

    # Provider dropdown
    # ── Provider-switching logic ───────────────────────────────────────────
    #   The selected value is passed directly to the backend as the
    #   "provider" field.  Adding a new provider = one new selectbox option.
    provider = st.selectbox(
        "🧠 AI Provider",
        options=["gemini", "groq"],
        format_func=lambda x: {
            "gemini": "✨ Google Gemini",
            "groq":   "⚡ Groq (GPT OSS 120B)",
        }[x],
        help="Choose which AI model answers your messages.",
    )

    # Show a badge reflecting current selection
    badge_color = {"gemini": "#4285F4", "groq": "#f55036"}.get(provider, "#6366f1")
    st.markdown(
        f'<span class="provider-badge">Active: {provider.upper()}</span>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("##### 💡 Tips")
    st.markdown(
        "- Press **Enter** to send\n"
        "- Switch provider mid-chat anytime\n"
        "- Each reply shows which model answered"
    )

    # Clear chat button
    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# ── Page title ────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='text-align:center; background: linear-gradient(135deg,#f1f5f9,#94a3b8);"
    "-webkit-background-clip:text;-webkit-text-fill-color:transparent;"
    "background-clip:text; margin-bottom:0;'>🤖 AI Chatbot</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center;color:#475569;font-size:0.85rem;margin-top:4px;'>"
    "Powered by Google Gemini &amp; Groq</p>",
    unsafe_allow_html=True,
)
st.markdown("---")


# ── Session state — message history ──────────────────────────────────────────
#   st.session_state persists data across Streamlit reruns (which happen on
#   every user interaction).  Think of it like a per-browser-tab store.
#   We store a list of {"role": "user"|"assistant", "content": "...", "provider": "..."}
if "messages" not in st.session_state:
    st.session_state.messages = []


# ── Render chat history ───────────────────────────────────────────────────────
#   st.chat_message("user") and st.chat_message("assistant") automatically
#   apply different bubble styles and avatars. We loop over ALL past messages
#   on every rerun so the history is always visible.
for msg in st.session_state.messages:
    avatar = "🧑‍💻" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        # Show a tiny provider badge under each bot reply
        if msg["role"] == "assistant" and msg.get("provider"):
            prov = msg["provider"]
            label = {"gemini": "✨ Gemini", "groq": "⚡ Groq"}.get(prov, prov)
            st.caption(f"Answered by **{label}**")


# ── Empty state ───────────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown(
        "<div style='text-align:center;color:#475569;padding:60px 0;font-size:1rem;'>"
        "💬 Select a provider in the sidebar and start chatting!"
        "</div>",
        unsafe_allow_html=True,
    )


# ── Chat input ────────────────────────────────────────────────────────────────
#   st.chat_input() renders a sticky input bar at the bottom of the page.
#   It returns the user's text when they press Enter, or None otherwise.
#   This is the idiomatic Streamlit way to build chat UIs (added in v1.25).
if prompt := st.chat_input("Ask anything…"):

    # 1. Add the user message to state and display it immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    # 2. Call the FastAPI backend and show a spinner while waiting
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking…"):
            try:
                # ── HTTP POST to /chat ─────────────────────────────────────
                #   We use the synchronous `requests` library here because
                #   Streamlit runs in a regular (non-async) Python thread.
                #   timeout=30 prevents hanging forever if the API is slow.
                response = requests.post(
                    API_URL,
                    json={"message": prompt, "provider": provider},
                    timeout=30,
                )
                response.raise_for_status()   # Raises for 4xx / 5xx responses
                data = response.json()
                reply    = data["reply"]
                answered_by = data.get("provider", provider)

            except requests.exceptions.ConnectionError:
                # Backend not running — give a helpful message, not a stack trace
                reply       = "⚠️ Cannot connect to the backend. Is `uvicorn main:app --reload` running on port 8000?"
                answered_by = None

            except requests.exceptions.Timeout:
                reply       = "⚠️ The request timed out. The AI provider may be slow — try again."
                answered_by = None

            except requests.exceptions.HTTPError as e:
                # FastAPI returns { "detail": "..." } for HTTPException errors
                detail = response.json().get("detail", str(e))
                reply  = f"⚠️ Backend error: {detail}"
                answered_by = None

        # 3. Display the reply
        st.markdown(reply)
        if answered_by:
            label = {"gemini": "✨ Gemini", "groq": "⚡ Groq"}.get(answered_by, answered_by)
            st.caption(f"Answered by **{label}**")

    # 4. Persist the assistant reply to session state
    st.session_state.messages.append({
        "role": "assistant",
        "content": reply,
        "provider": answered_by,
    })
