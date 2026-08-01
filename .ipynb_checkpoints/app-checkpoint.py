import streamlit as st

from database.enums import UserRole
from services.auth_service import (
    authenticate_user,
    update_last_seen,
)

from views.admin import show as admin_dashboard
from views.annotator import show as annotator_dashboard
from views.reviewer import show as reviewer_dashboard


# -------------------------------------------------
# Page Configuration
# -------------------------------------------------
st.set_page_config(
    page_title="Akshara",
    page_icon="🎙️",
    layout="wide"
)


# -------------------------------------------------
# Session Initialization
# -------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None


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
            st.rerun()

        st.error("Invalid username or password.")


# -------------------------------------------------
# Dashboard Router
# -------------------------------------------------
def dashboard():

    user = st.session_state.user

    update_last_seen(user.id)

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