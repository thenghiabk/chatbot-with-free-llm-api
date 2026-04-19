import os
import uuid
import time
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# --- Page Config ---
st.set_page_config(page_title="NVIDIA AI Chatbot", page_icon="🟢", layout="wide")

# --- Config ---
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL")

DEFAULT_GREETING = "Hello! How can I help you today?"


def get_client() -> OpenAI:
    return OpenAI(base_url=NVIDIA_BASE_URL, api_key=NVIDIA_API_KEY)


def call_nvidia_stream(messages: list[dict]):
    """Stream response from NVIDIA API; yields (reasoning_chunk, content_chunk) tuples."""
    client = get_client()
    completion = client.chat.completions.create(
        model=NVIDIA_MODEL,
        messages=messages,
        temperature=0.2,
        top_p=0.7,
        max_tokens=8192,
        extra_body={"chat_template_kwargs": {"thinking": False}},
        stream=True
    )
    for chunk in completion:
        if not getattr(chunk, "choices", None):
            continue
        delta = chunk.choices[0].delta
        reasoning = getattr(delta, "reasoning_content", None)
        content = delta.content if delta.content is not None else ""
        yield reasoning or "", content


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
    system_prompt = os.getenv("SYSTEM_PROMPT", "")
    materials_context = "\n\n".join(f"--- {fn} ---\n{ct}" for fn, ct in materials)
    parts = []
    if system_prompt:
        parts.append(system_prompt)
    if materials_context:
        parts.append(f"Reference materials:\n{materials_context}")
    return "\n\n".join(parts) if parts else None


def get_greeting(materials: list[tuple]) -> str:
    if not materials or not NVIDIA_API_KEY:
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
        reply = ""
        for _, content in call_nvidia_stream(messages):
            reply += content
        return reply.strip() or os.getenv("GREETING_MESSAGE", DEFAULT_GREETING)
    except Exception:
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


# --- Styles ---
st.markdown("""
<style>
[data-testid="stMainBlockContainer"] {
    padding-top:    1rem   !important;
    padding-bottom: 80px   !important;
    box-sizing: border-box !important;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    height:     calc(100vh - 220px) !important;
    max-height: calc(100vh - 220px) !important;
    overflow-y: auto  !important;
    overflow-x: hidden !important;
}
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
    st.markdown("# 🟢 NVIDIA AI Chatbot")
    st.caption(f"Model: `{NVIDIA_MODEL}`")
    active = get_active()

    chat_container = st.container(height=PANEL_HEIGHT, border=False)
    with chat_container:
        for msg in active["messages"]:
            with st.chat_message(msg["role"]):
                # Show stored reasoning in an expander if present
                if msg.get("reasoning"):
                    with st.expander("🧠 Reasoning", expanded=False):
                        st.markdown(msg["reasoning"])
                st.markdown(msg["content"])

# --- Chat Input ---
prompt = st.chat_input("Type your message...")

if prompt:
    if not NVIDIA_API_KEY:
        st.warning("NVIDIA API key is not configured. Set `NVIDIA_API_KEY` in your `.env` file.")
    else:
        active["messages"].append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    api_messages = []
                    system_msg = build_system_message(materials)
                    if system_msg:
                        api_messages.append({"role": "system", "content": system_msg})
                    for msg in active["messages"]:
                        api_messages.append({"role": msg["role"], "content": msg["content"]})

                    thinking_placeholder = st.empty()
                    thinking_placeholder.markdown("_Thinking…_")

                    reasoning_placeholder = st.empty()
                    content_placeholder = st.empty()

                    full_reasoning = ""
                    full_content = ""

                    for reasoning_chunk, content_chunk in call_nvidia_stream(api_messages):
                        thinking_placeholder.empty()
                        if reasoning_chunk:
                            full_reasoning += reasoning_chunk
                            with reasoning_placeholder.expander("🧠 Reasoning", expanded=True):
                                st.markdown(full_reasoning)
                        if content_chunk:
                            full_content += content_chunk
                            content_placeholder.markdown(full_content)

                    active["messages"].append({
                        "role": "assistant",
                        "content": full_content,
                        "reasoning": full_reasoning,
                    })

                except Exception as e:
                    st.error(f"Error: {e}")

