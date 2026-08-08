import streamlit as st

from database.enums import UserRole
from services.auth_service import (
    authenticate_user,
    update_last_seen,
)

from views.admin import show as admin_dashboard
from views.annotator import show as annotator_dashboard
from views.reviewer import show as reviewer_dashboard

from services.session_service import (
    create_session,
    get_user_from_token,
    set_session_cookie,
    clear_session_cookie,
    read_session_cookie,
)


# -------------------------------------------------
# Page Configuration
# -------------------------------------------------
st.set_page_config(
    page_title="Akshara",
    page_icon="🎙️",
    layout="wide"
)

# -------------------------------------------------
# Database Initialization
# -------------------------------------------------
# Automatically create DB schema and default admin user if they don't exist
# This ensures cloud deployments work immediately without manual setup scripts
from database.init_db import initialize_database
initialize_database()


# -------------------------------------------------
# Cookie Injection (must run before rendering UI)
# -------------------------------------------------
if st.session_state.get("pending_logout_cookie"):
    clear_session_cookie()
    del st.session_state["pending_logout_cookie"]

if st.session_state.get("pending_login_cookie"):
    set_session_cookie(st.session_state["pending_login_cookie"])
    del st.session_state["pending_login_cookie"]


# -------------------------------------------------
# Session Initialization
# -------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None
    
    # Attempt to restore session from browser cookie
    cookie_token = read_session_cookie()
    if cookie_token:
        user = get_user_from_token(cookie_token)
        if user:
            st.session_state.user = user
            st.session_state.session_token = cookie_token


# -------------------------------------------------
# Login Page
# -------------------------------------------------
def login_page():
    st.title("🎙️ Akshara")

    with st.form("login_form"):

        username = st.text_input("Username")

        password = st.text_input(
            "Password",
            type="password"
        )

        submitted = st.form_submit_button("Login")

    if submitted:

        user = authenticate_user(username, password)

        if user:
            st.session_state.user = user
            raw_token = create_session(user.id)
            st.session_state.session_token = raw_token
            st.session_state.pending_login_cookie = raw_token
            st.rerun()

        st.error("Invalid username or password.")


# -------------------------------------------------
# Dashboard Router
# -------------------------------------------------
def dashboard():

    user = st.session_state.user

    try:
        update_last_seen(user.id)
    except Exception:
        # Ignore last seen update failures to prevent dashboard crash
        pass

    if user.role == UserRole.ADMIN:
        admin_dashboard()

    elif user.role == UserRole.ANNOTATOR:
        annotator_dashboard()

    elif user.role == UserRole.REVIEWER:
        reviewer_dashboard()

    else:
        st.error("Unknown user role.")


# -------------------------------------------------
# Application Entry Point
# -------------------------------------------------
if st.session_state.user is None:
    login_page()
else:
    dashboard()