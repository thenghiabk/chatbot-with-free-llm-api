import os
import uuid
import time
import streamlit as st
from dotenv import load_dotenv
from gemini import Gemini

load_dotenv()

# --- Page Config ---
st.set_page_config(page_title="Gemini Chatbot", page_icon="🤖", layout="wide")

# --- Auto-connect (hidden from user) ---
if "client" not in st.session_state:
    env_psid = os.getenv("SECURE_1PSID", "")
    env_psidts = os.getenv("SECURE_1PSIDTS", "")
    env_psidcc = os.getenv("SECURE_1PSIDCC", "")
    if env_psid and env_psidts and env_psidcc:
        st.session_state.client = Gemini(cookies={
            "__Secure-1PSID": env_psid,
            "__Secure-1PSIDTS": env_psidts,
            "__Secure-1PSIDCC": env_psidcc,
        })

# --- Session init (hidden from user) ---
DEFAULT_GREETING = "Hello! How can I help you today?"

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

def get_greeting():
    """Generate a greeting question based on available materials."""
    mats = load_materials()
    if not mats:
        return os.getenv("GREETING_MESSAGE", DEFAULT_GREETING)
    if "client" in st.session_state:
        try:
            system_prompt = os.getenv("SYSTEM_PROMPT", "")
            materials_context = "\n\n".join(f"--- {fn} ---\n{ct}" for fn, ct in mats)
            sections = []
            if system_prompt:
                sections.append(system_prompt)
            sections.append(f"Reference materials:\n{materials_context}")
            sections.append(
                "Based on the reference materials above, greet the user and ask ONE relevant question to start the conversation. Be concise."
            )
            full_prompt = "\n\n".join(sections)
            response = st.session_state.client.generate_content(full_prompt)
            reply = response if isinstance(response, str) else response.text
            return reply.strip()
        except Exception:
            pass
    return os.getenv("GREETING_MESSAGE", DEFAULT_GREETING)

if "chat_sessions" not in st.session_state:
    with st.spinner("Loading, please wait…"):
        default_id = str(uuid.uuid4())
        greeting = get_greeting()
        st.session_state.chat_sessions = {
            default_id: {"name": "Chat 1", "messages": [{"role": "assistant", "content": greeting}]}
        }
        st.session_state.active_session = default_id

if "active_session" not in st.session_state:
    st.session_state.active_session = next(iter(st.session_state.chat_sessions))

def get_active():
    return st.session_state.chat_sessions[st.session_state.active_session]


def stream_text(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.03)

# --- Fix chat input to bottom of screen ---
st.markdown("""
<style>
.stChatInput {
    position: fixed;
    bottom: 3rem;
    z-index: 999;
    width: 55%;
}
</style>
""", unsafe_allow_html=True)

# --- Layout ---
materials = load_materials()
left, right = st.columns([2, 3], gap="large")

# --- Left: Materials Panel ---
with left:
    st.markdown("## 📚 Materials")
    st.divider()
    if not materials:
        st.info("No materials found. Add files to the `materials/` folder.")
    else:
        for filename, content in materials:
            with st.expander(f"📄 {filename}", expanded=True):
                st.code(content, language="python")

# --- Right: Chat Panel ---
with right:
    st.markdown("## 🤖 Gemini Chatbot")
    st.divider()

    active = get_active()

    # Scrollable chat history in fixed-height container
    chat_container = st.container(height=500, border=False)
    with chat_container:
        for msg in active["messages"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Chat input always at bottom
    if prompt := st.chat_input("Type your message..."):
        if "client" not in st.session_state:
            st.warning("Chatbot is not configured. Please contact the administrator.")
        else:
            active["messages"].append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            system_prompt = os.getenv("SYSTEM_PROMPT", "")
                            materials_context = "\n\n".join(
                                f"--- {fn} ---\n{ct}" for fn, ct in materials
                            )
                            history = ""
                            for msg in active["messages"][:-1]:
                                role = "User" if msg["role"] == "user" else "Assistant"
                                history += f"{role}: {msg['content']}\n"

                            sections = []
                            if system_prompt:
                                sections.append(system_prompt)
                            if materials_context:
                                sections.append(f"Reference materials:\n{materials_context}")
                            if history:
                                sections.append(history)
                            sections.append(f"User: {prompt}\nAssistant:")
                            full_prompt = "\n\n".join(sections)

                            response = st.session_state.client.generate_content(full_prompt)
                            reply = response if isinstance(response, str) else response.text
                            st.write_stream(stream_text(reply))
                            active["messages"].append({"role": "assistant", "content": reply})
                        except Exception as e:
                            st.error(f"Error: {e}")
