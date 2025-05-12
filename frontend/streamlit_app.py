import streamlit as st
import requests

API_URL = "http://192.168.1.22:8000"

st.set_page_config(layout="wide", page_title="PDF ChatGPT")

# --- Session State Initialization ---
if "pdf_files" not in st.session_state:
    st.session_state["pdf_files"] = {}  # {filename: file_bytes}
if "chat_histories" not in st.session_state:
    st.session_state["chat_histories"] = {}  # {filename: [{"role": "user"/"bot", "msg": ...}]}
if "selected_pdf" not in st.session_state:
    st.session_state["selected_pdf"] = None
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

def toggle_theme():
    st.session_state["theme"] = "light" if st.session_state["theme"] == "dark" else "dark"

st.sidebar.button("🌗 Toggle Theme", on_click=toggle_theme)

# --- Sidebar: Upload and List PDFs ---
st.sidebar.header("📄 Uploaded PDFs")
uploaded_file = st.sidebar.file_uploader("Upload PDF", type=["pdf"], key="pdf_uploader")
if uploaded_file:
    st.session_state["pdf_files"][uploaded_file.name] = uploaded_file.getvalue()
    st.session_state["chat_histories"].setdefault(uploaded_file.name, [])
    st.session_state["selected_pdf"] = uploaded_file.name
    files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
    response = requests.post(f"{API_URL}/upload", files=files)
    if response.ok:
        st.sidebar.success(f"Uploaded: {uploaded_file.name}")
    else:
        st.sidebar.error("Failed to upload/process PDF.")

for fname in list(st.session_state["pdf_files"].keys()):
    col1, col2 = st.sidebar.columns([8, 1])
    if col1.button(fname, key=f"select_{fname}"):
        st.session_state["selected_pdf"] = fname
    if col2.button("🗑️", key=f"delete_{fname}"):
        del st.session_state["pdf_files"][fname]
        del st.session_state["chat_histories"][fname]
        if st.session_state["selected_pdf"] == fname:
            st.session_state["selected_pdf"] = next(iter(st.session_state["pdf_files"]), None)
        st.rerun()

# --- Main Chat Area ---
def chat_bubble(message, is_user, theme):
    align = "flex-end" if is_user else "flex-start"
    bg = "#0059b2" if is_user else ("#262730" if theme == "dark" else "#f0f0f0")
    color = "#fff" if is_user or theme == "dark" else "#000"
    border_radius = "20px 20px 5px 20px" if is_user else "20px 20px 20px 5px"
    html = f"""
    <div style='display: flex; justify-content: {align}; margin-bottom: 8px;'>
        <div style='background: {bg}; color: {color}; padding: 12px 18px; border-radius: {border_radius}; max-width: 70%; font-size: 1.1em;'>
            {message}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {"#18191A" if st.session_state["theme"] == "dark" else "#fff"};
        color: {"#fff" if st.session_state["theme"] == "dark" else "#000"};
    }}
    </style>
    """, unsafe_allow_html=True
)

st.title("🤖 PDF ChatGPT")

if st.session_state["selected_pdf"]:
    fname = st.session_state["selected_pdf"]
    st.subheader(f"Chatting with: {fname}")
    chat_history = st.session_state["chat_histories"][fname]

    # --- Chat Display ---
    chat_container = st.container()
    for entry in chat_history:
        chat_bubble(entry["msg"], entry["role"] == "user", st.session_state["theme"])

    # --- Chat Input ---
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("Type your message...", key="user_input")
        send = st.form_submit_button("Send")
        if send and user_input.strip():
            chat_history.append({"role": "user", "msg": user_input})
            data = {"query": user_input}
            response = requests.post(f"{API_URL}/chat", data=data)
            if response.ok:
                result = response.json()
                bot_msg = result["answer"]
            else:
                bot_msg = "Sorry, there was an error."
            chat_history.append({"role": "bot", "msg": bot_msg})
            st.rerun()
else:
    st.info("Upload a PDF to start chatting!") 