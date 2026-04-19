import os
import uuid
import time
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# --- Page Config ---
st.set_page_config(page_title="OpenRouter Chatbot", page_icon="🤖", layout="wide")

# --- Config ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

DEFAULT_GREETING = "Hello! How can I help you today?"

# Fallback list in case live fetch fails
_FREE_MODEL_FALLBACKS = [
    "meta-llama/llama-3.1-8b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "google/gemma-3-12b-it:free",
    "microsoft/phi-3-mini-128k-instruct:free",
    "openchat/openchat-7b:free",
]


@st.cache_data(ttl=3600, show_spinner=False)
def resolve_model(env_model: str) -> str:
    """Return env-specified model if set, otherwise pick first available :free model."""
    if env_model:
        return env_model
    try:
        resp = requests.get(
            OPENROUTER_MODELS_URL,
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            timeout=10,
        )
        if resp.ok:
            ids = [m["id"] for m in resp.json().get("data", []) if ":free" in m["id"]]
            if ids:
                return sorted(ids)[0]
    except Exception:
        pass
    return _FREE_MODEL_FALLBACKS[0]


# OPENROUTER_MODEL = resolve_model(os.getenv("OPENROUTER_MODEL", ""))
OPENROUTER_MODEL = "openai/gpt-oss-120b:free"


def call_openrouter(messages: list[dict]) -> str:
    """Send messages to OpenRouter and return the assistant reply."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/local/chatbot",
        "X-Title": "OpenRouter Chatbot",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
    }
    response = requests.post(OPENROUTER_API_URL, json=payload, headers=headers, timeout=60)
    if response.status_code == 429:
        try:
            err = response.json().get("error", {})
            msg = err.get("message", "Rate limit exceeded.")
            reset_ms = err.get("metadata", {}).get("headers", {}).get("X-RateLimit-Reset")
            if reset_ms:
                import datetime
                reset_dt = datetime.datetime.fromtimestamp(int(reset_ms) / 1000)
                msg += f"\n\n⏰ Limit resets at **{reset_dt.strftime('%Y-%m-%d %H:%M:%S')}** (local time)."
        except Exception:
            msg = "Rate limit exceeded. Please try again later or add credits to your OpenRouter account."
        raise Exception(f"🚫 Rate limit reached:\n\n{msg}")
    if not response.ok:
        raise Exception(f"HTTP {response.status_code}: {response.text}")
    data = response.json()
    return data["choices"][0]["message"]["content"]


def load_materials():
    """Read all files from the materials/ folder and return list of (filename, content)."""
    materials_dir = os.path.join(os.path.dirname(__file__), "materials")
    if not os.path.isdir(materials_dir):
        return []
    files = []
    for filename in sorted(os.listdir(materials_dir)):
        filepath = os.path.join(materials_dir, filename)
        if os.path.isfile(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content:
                    files.append((filename, content))
            except Exception:
                pass
    return files


def build_system_message(materials: list[tuple]) -> str | None:
    """Build a system message from SYSTEM_PROMPT env var and materials."""
    system_prompt = os.getenv("SYSTEM_PROMPT", "")
    materials_context = "\n\n".join(f"--- {fn} ---\n{ct}" for fn, ct in materials)
    parts = []
    if system_prompt:
        parts.append(system_prompt)
    if materials_context:
        parts.append(f"Reference materials:\n{materials_context}")
    return "\n\n".join(parts) if parts else None


def get_greeting(materials: list[tuple]) -> str:
    """Generate a greeting question based on available materials."""
    if not materials or not OPENROUTER_API_KEY:
        return os.getenv("GREETING_MESSAGE", DEFAULT_GREETING)
    try:
        system_msg = build_system_message(materials)
        messages = []
        if system_msg:
            messages.append({"role": "system", "content": system_msg})
        messages.append({
            "role": "user",
            "content": "Greet the user and ask ONE relevant question to start the conversation. Be concise.",
        })
        return call_openrouter(messages).strip()
    except Exception as e:
        if "Rate limit" in str(e) or "429" in str(e):
            return "⚠️ OpenRouter free-model daily limit reached. Add credits or wait until midnight UTC to continue."
        return os.getenv("GREETING_MESSAGE", DEFAULT_GREETING)


# --- Session init ---
if "chat_sessions" not in st.session_state:
    with st.spinner("Loading, please wait…"):
        mats = load_materials()
        default_id = str(uuid.uuid4())
        greeting = get_greeting(mats)
        st.session_state.chat_sessions = {
            default_id: {"name": "Chat 1", "messages": [{"role": "assistant", "content": greeting}]}
        }
        st.session_state.active_session = default_id

if "active_session" not in st.session_state:
    st.session_state.active_session = next(iter(st.session_state.chat_sessions))


def get_active():
    return st.session_state.chat_sessions[st.session_state.active_session]


def stream_text(text: str):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.03)


# --- Styles ---
st.markdown("""
<style>
/* ── Reserve space at the bottom for the fixed input bar ── */
[data-testid="stMainBlockContainer"] {
    padding-top:    1rem   !important;
    padding-bottom: 80px   !important;
    box-sizing: border-box !important;
}

/* ── Panel containers: scrollable, fill most of the viewport ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    height:     calc(100vh - 220px) !important;
    max-height: calc(100vh - 220px) !important;
    overflow-y: auto  !important;
    overflow-x: hidden !important;
}

/* ── Fixed chat-input bar at the bottom ── */
[data-testid="stBottom"] {
    position:   fixed  !important;
    bottom:     0      !important;
    left:       0      !important;
    right:      0      !important;
    height:     56px   !important;
    z-index:    1000   !important;
    background: var(--background-color, #0e1117) !important;
    border-top: 1px solid rgba(128,128,128,0.25) !important;
    padding:    0.25rem 1.5rem !important;
    display:    flex   !important;
    align-items: center !important;
}
</style>
""", unsafe_allow_html=True)

# Small value – Streamlit needs a non-zero number to emit the scrollable wrapper;
# the CSS calc() above sets the real height.
PANEL_HEIGHT = 650

# --- Layout ---
materials = load_materials()
left, right = st.columns([2, 3], gap="large")

# --- Left: Materials Panel ---
with left:
    st.markdown("# 📚 Materials")
    with st.container(height=PANEL_HEIGHT, border=False):
        if not materials:
            st.info("No materials found. Add files to the `materials/` folder.")
        else:
            ext_to_lang = {
                ".py": "python", ".js": "javascript", ".ts": "typescript",
                ".jsx": "jsx", ".tsx": "tsx", ".html": "html", ".css": "css",
                ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".toml": "toml",
                ".md": "markdown", ".sh": "bash", ".bat": "batch", ".ps1": "powershell",
                ".sql": "sql", ".java": "java", ".c": "c", ".cpp": "cpp",
                ".cs": "csharp", ".go": "go", ".rs": "rust", ".rb": "ruby",
                ".php": "php", ".swift": "swift", ".kt": "kotlin", ".r": "r",
                ".xml": "xml", ".txt": "text",
            }
            for filename, content in materials:
                ext = os.path.splitext(filename)[1].lower()
                lang = ext_to_lang.get(ext, "text")
                with st.expander(f"📄 {filename}", expanded=True):
                    st.code(content, language=lang)

# --- Right: Chat Panel ---
with right:
    st.markdown("# 🤖 OpenRouter Chatbot")
    st.caption(f"Model: `{OPENROUTER_MODEL}`")
    active = get_active()

    chat_container = st.container(height=PANEL_HEIGHT, border=False)
    with chat_container:
        for msg in active["messages"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

# chat_input outside columns → Streamlit pins it to the bottom of the page
prompt = st.chat_input("Type your message...")

if prompt:
    if not OPENROUTER_API_KEY:
        st.warning("OpenRouter API key is not configured. Set `OPENROUTER_API_KEY` in your `.env` file.")
    else:
        active["messages"].append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        api_messages = []
                        system_msg = build_system_message(materials)
                        if system_msg:
                            api_messages.append({"role": "system", "content": system_msg})
                        for msg in active["messages"]:
                            api_messages.append({"role": msg["role"], "content": msg["content"]})

                        reply = call_openrouter(api_messages)
                        st.write_stream(stream_text(reply))
                        active["messages"].append({"role": "assistant", "content": reply})
                    except Exception as e:
                        st.error(f"Error: {e}")

