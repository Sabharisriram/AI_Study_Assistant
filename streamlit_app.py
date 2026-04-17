import streamlit as st
import requests
import time
import os

# ✅ Reads from Streamlit secrets in cloud, falls back to localhost for local dev
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="AI Study Assistant", layout="wide")

st.markdown("""
<style>
.main { background-color: #0E1117; }
.block-container { max-width: 900px; margin: auto; padding-top: 2rem; }
.header { text-align: center; font-size: 32px; font-weight: bold; margin-bottom: 20px; }
.user { background-color: #2563eb; padding: 12px; border-radius: 12px; margin: 10px 0; color: white; }
.assistant { background-color: #1e293b; padding: 12px; border-radius: 12px; margin: 10px 0; }
section[data-testid="stSidebar"] { background-color: #111827; }
</style>
""", unsafe_allow_html=True)

if "token"           not in st.session_state: st.session_state.token           = None
if "user_email"      not in st.session_state: st.session_state.user_email      = None
if "messages"        not in st.session_state: st.session_state.messages        = []
if "uploaded_pdfs"   not in st.session_state: st.session_state.uploaded_pdfs   = set()
if "uploaded_images" not in st.session_state: st.session_state.uploaded_images = set()


def auth_header() -> dict:
    return {"Authorization": f"Bearer {st.session_state.token}"}


# ══════════════════════════════════════════════════════════════════
# AUTH PAGE
# ══════════════════════════════════════════════════════════════════
if st.session_state.token is None:

    st.markdown("<div class='header'>🤖 AI Study Assistant</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

        with tab_login:
            st.markdown("#### Welcome back")
            email    = st.text_input("Email",    key="login_email")
            password = st.text_input("Password", type="password", key="login_password")

            if st.button("Login", use_container_width=True):
                if not email or not password:
                    st.error("Please enter email and password")
                else:
                    try:
                        res = requests.post(
                            f"{API_URL}/auth/login",
                            json={"email": email, "password": password},
                            timeout=15
                        )
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state.token      = data["access_token"]
                            st.session_state.user_email = data["email"]
                            st.session_state.messages   = []
                            st.rerun()
                        else:
                            st.error(f"Login failed: {res.json().get('detail', 'Unknown error')}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to backend.")

        with tab_signup:
            st.markdown("#### Create account")
            new_email    = st.text_input("Email",            key="signup_email")
            new_password = st.text_input("Password (min 6)", type="password", key="signup_password")

            if st.button("Create Account", use_container_width=True):
                if not new_email or not new_password:
                    st.error("Please fill all fields")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    try:
                        res = requests.post(
                            f"{API_URL}/auth/signup",
                            json={"email": new_email, "password": new_password},
                            timeout=15
                        )
                        if res.status_code == 200:
                            st.success("✅ Account created! Please log in.")
                        else:
                            st.error(f"Signup failed: {res.json().get('detail', 'Unknown error')}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to backend.")

    st.stop()


# ══════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════
st.markdown("<div class='header'>🤖 AI Study Assistant</div>", unsafe_allow_html=True)

st.sidebar.markdown(f"👤 **{st.session_state.user_email}**")
if st.sidebar.button("Logout"):
    requests.post(f"{API_URL}/auth/logout", headers=auth_header())
    st.session_state.token           = None
    st.session_state.user_email      = None
    st.session_state.messages        = []
    st.session_state.uploaded_pdfs   = set()
    st.session_state.uploaded_images = set()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("## 📂 Upload Files")

pdf_file   = st.sidebar.file_uploader("📄 Upload PDF",   type=["pdf"])
image_file = st.sidebar.file_uploader("🖼 Upload Image", type=["png","jpg","jpeg"])

if pdf_file and pdf_file.name not in st.session_state.uploaded_pdfs:
    with st.sidebar, st.spinner("Indexing PDF..."):
        try:
            res = requests.post(
                f"{API_URL}/pdf/upload-pdf",
                files={"file": (pdf_file.name, pdf_file.getvalue(), "application/pdf")},
                headers=auth_header(),
                timeout=120
            )
            if res.status_code == 200:
                data = res.json()
                st.session_state.uploaded_pdfs.add(pdf_file.name)
                st.success(f"✅ {data.get('chunks','?')} chunks indexed")
            else:
                st.error(f"❌ {res.status_code}: {res.text}")
        except Exception as e:
            st.error(f"❌ {e}")

if image_file and image_file.name not in st.session_state.uploaded_images:
    with st.sidebar, st.spinner("Processing image..."):
        try:
            res = requests.post(
                f"{API_URL}/image/upload-image",
                files={"file": (image_file.name, image_file.getvalue(), image_file.type)},
                headers=auth_header(),
                timeout=120
            )
            if res.status_code == 200:
                data = res.json()
                st.session_state.uploaded_images.add(image_file.name)
                st.success(f"✅ {data.get('chunks','?')} chunks indexed")
            else:
                st.error(f"❌ {res.status_code}: {res.text}")
        except Exception as e:
            st.error(f"❌ {e}")

if st.session_state.uploaded_pdfs:
    st.sidebar.markdown("**Indexed PDFs:**")
    for name in st.session_state.uploaded_pdfs:
        st.sidebar.markdown(f"- 📄 {name}")

if st.session_state.uploaded_images:
    st.sidebar.markdown("**Indexed Images:**")
    for name in st.session_state.uploaded_images:
        st.sidebar.markdown(f"- 🖼 {name}")

st.sidebar.markdown("---")
st.sidebar.info("💡 Upload files and ask questions!")

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='user'>👤 {msg['content']}</div>", unsafe_allow_html=True)
    else:
        formatted = msg["content"].replace("\n", "<br>")
        st.markdown(f"<div class='assistant'>🤖 {formatted}</div>", unsafe_allow_html=True)

prompt = st.chat_input("Ask anything...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(f"<div class='user'>👤 {prompt}</div>", unsafe_allow_html=True)

    placeholder   = st.empty()
    full_response = ""
    placeholder.markdown("<div class='assistant'>🤖 Thinking...</div>", unsafe_allow_html=True)

    try:
        response = requests.post(
            f"{API_URL}/chat/stream",
            json={"question": prompt},
            headers=auth_header(),
            stream=True,
            timeout=120
        )

        if response.status_code == 401:
            st.warning("Session expired. Please log in again.")
            st.session_state.token = None
            st.rerun()
        elif response.status_code != 200:
            full_response = f"⚠️ Backend error: {response.status_code}"
        else:
            for chunk in response.iter_content(chunk_size=20):
                if chunk:
                    full_response += chunk.decode("utf-8")
                    formatted = full_response.replace("\n", "<br>")
                    placeholder.markdown(
                        f"<div class='assistant'>🤖 {formatted}</div>",
                        unsafe_allow_html=True
                    )
                    time.sleep(0.01)

    except requests.exceptions.ConnectionError:
        full_response = "⚠️ Cannot connect to backend."
    except requests.exceptions.Timeout:
        full_response = "⚠️ Request timed out."
    except Exception as e:
        full_response = f"⚠️ Error: {str(e)}"

    placeholder.markdown(
        f"<div class='assistant'>🤖 {full_response.replace(chr(10),'<br>')}</div>",
        unsafe_allow_html=True
    )
    st.session_state.messages.append({"role": "assistant", "content": full_response})