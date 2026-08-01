import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

import zipfile
import uuid
import shutil
from pathlib import Path

from database.enums import UserRole

from utils.time import now

from services.user_service import (
    create_user,
    get_all_users,
    update_user,
    delete_user,
)

from services.audio_service import (
    upload_audio,
    get_all_datasets,
    get_dataset_files,
    delete_audio
)

from services.assignment_service import (
    get_unassigned_audio,
    get_annotators,
    assign_audio,
    get_assignments,
    unassign_audio
)

from utils.logout import logout

# =====================================================
# Dashboard
# =====================================================
def dashboard():

    col1, col2 = st.columns([8, 1])

    with col1:
        st.title("Admin Dashboard")

    with col2:
        if st.button("Logout", width="stretch"):
            logout()
            
    st.write(f"Welcome, **{st.session_state.user.username}**")

    st.divider()

    c1, c2 = st.columns(2)

    with c1:

        if st.button("👤 User Management", use_container_width=True):
            st.session_state.admin_page = "users"
            st.rerun()

        if st.button("📂 Assignments", use_container_width=True):
            st.session_state.admin_page = "assignments"
            st.rerun()

    with c2:

        if st.button("🎙️ Audio Library", use_container_width=True):
            st.session_state.admin_page = "audio"
            st.rerun()

        if st.button("📊 Analytics", use_container_width=True):
            st.session_state.admin_page = "analytics"
            st.rerun()


# =====================================================
# Users
# =====================================================
def users():

    st.title("👤 User Management")

    if "editing_user" not in st.session_state:
        st.session_state.editing_user = None

    if "delete_user" not in st.session_state:
        st.session_state.delete_user = None
    
    users_list = get_all_users()

    c1, c2 = st.columns([2,1])

    with c1:
        search = st.text_input(
            "Search",
            placeholder="Username or Email"
        )

    with c2:
        role_filter = st.selectbox(
            "Role",
            [
                "All",
                "Admin",
                "Annotator",
                "Reviewer"
            ]
        )

    filtered_users = []

    for user in users_list:

        if search:

            if (
                search.lower() not in user.username.lower()
                and
                search.lower() not in user.email.lower()
            ):
                continue

        if role_filter != "All":

            if user.role.value.title() != role_filter:
                continue

        filtered_users.append(user)

    users_list = filtered_users
    
    if users_list:

        for user in users_list:

            c1, c2, c3, c4 = st.columns([3,2,2,2])

            with c1:
                st.markdown(f"### {user.username}")
                st.caption(user.email)

            with c2:

                st.write(user.role.value.title())
    
                if user.last_seen:

                    if now() - user.last_seen < timedelta(minutes=2):

                        st.success("🟢 Online")

                    else:

                        st.caption("⚫ Offline")

                else:

                    st.caption("Never Logged In")

            with c3:

                if user.last_login:
                    st.write(
                        user.last_login.strftime("%d-%m-%Y")
                    )
                    st.caption(
                        user.last_login.strftime("%I:%M %p")
                    )
                else:
                    st.caption("-")
    
            with c4:

                if st.button(
                    "✏ Edit",
                    key=f"edit_{user.id}"
                ):
                    st.session_state.editing_user = user.id

                if (
                    user.id
                    !=
                    st.session_state.user.id
                ):

                    if st.button(
                        "🗑 Delete",
                        key=f"delete_{user.id}"
                    ):
                        st.session_state.delete_user = user.id

        st.divider()

    else:
        st.info("No users found.")

    if st.session_state.editing_user:

        selected = next(
            (
                u
                for u in users_list
                if u.id == st.session_state.editing_user
            ),
            None
        )

        if selected:

            st.subheader("Edit User")

            with st.form("edit_user"):
    
                username = st.text_input(
                    "Username",
                    value=selected.username
                )

                email = st.text_input(
                    "Email",
                    value=selected.email
                )

                role = st.selectbox(
                    "Role",
                    [
                        UserRole.ADMIN,
                        UserRole.ANNOTATOR,
                        UserRole.REVIEWER
                    ],
                    index=[
                        UserRole.ADMIN,
                        UserRole.ANNOTATOR,
                        UserRole.REVIEWER
                    ].index(selected.role)
                )

                c1, c2 = st.columns(2)

                save = c1.form_submit_button("Save")

                cancel = c2.form_submit_button("Cancel")
    
            if save:

                success, message = update_user(
                    selected.id,
                    username.strip(),
                    email.strip(),
                    role
                )

                if success:

                    st.success(message)

                    st.session_state.editing_user = None

                    st.rerun()

                else:

                    st.error(message)

            if cancel:

                st.session_state.editing_user = None

                st.rerun()
            
    st.divider()

    if st.session_state.delete_user:

        st.warning(
            "Delete this user?"
        )

        c1, c2 = st.columns(2)

        if c1.button("Yes"):

            success, message = delete_user(
                st.session_state.delete_user,
                st.session_state.user.id
            )

            if success:

                st.success(message)

            else:

                st.error(message)

            st.session_state.delete_user = None

            st.rerun()

        if c2.button("No"):

            st.session_state.delete_user = None

            st.rerun()
    
    st.divider()

    st.subheader("Create User")

    with st.form("create_user"):

        username = st.text_input("Username")

        email = st.text_input("Email")

        password = st.text_input(
            "Password",
            type="password"
        )

        confirm = st.text_input(
            "Confirm Password",
            type="password"
        )

        role = st.selectbox(
            "Role",
            [
                UserRole.ADMIN,
                UserRole.ANNOTATOR,
                UserRole.REVIEWER
            ],
            format_func=lambda x: x.value.title()
        )

        submitted = st.form_submit_button("Create User")

    if submitted:

        if not username or not email or not password or not confirm:

            st.error("Fill all fields.")

        elif password != confirm:

            st.error("Passwords do not match.")

        else:

            user = create_user(
                username=username.strip(),
                email=email.strip(),
                password=password,
                role=role
            )

            if user:

                st.success("User created successfully.")

                st.rerun()

            else:

                st.error("Username or Email already exists.")

    st.divider()

    if st.button("← Back"):

        st.session_state.admin_page = "dashboard"

        st.rerun()


# =====================================================
# Audio Library
# =====================================================
def audio():

    st.title("🎙️ Audio Library")

    if "upload_form_key" not in st.session_state:
        st.session_state.upload_form_key = 0
    
    with st.form(f"upload_audio_{st.session_state.upload_form_key}"):
        
        uploaded_file = st.file_uploader(
            "Upload Audio Dataset (.zip)",
            type=["zip"]
        )

        language = st.selectbox(
            "Language",
            [
                "English",
                "Hindi",
                "Telugu"
            ]
        )

        submit = st.form_submit_button("Upload")

    if submit:

        if uploaded_file is None:

            st.error("Please select an audio file.")

        else:

            success = upload_audio(
                uploaded_file,
                language,
                st.session_state.user.id
            )

            if success:

                st.success("Audio uploaded successfully.")

                st.session_state.upload_form_key += 1

                st.rerun()

            else:

                st.error("Upload failed.")

    st.divider()

    datasets = get_all_datasets()

    if not datasets:
        st.info("No datasets uploaded yet.")

    else:

        total_files = sum(d.total_files for d in datasets)
        total_size = sum(d.total_size for d in datasets)

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("Datasets", len(datasets))

        with c2:
            st.metric("Total Files", total_files)

        with c3:
            st.metric("Total Size (MB)", round(total_size, 2))

        st.divider()
    
        for dataset in datasets:

            with st.expander(
                f"📁 {dataset.name} | {dataset.total_files} files | {dataset.total_size:.2f} MB"
            ):

                st.write(f"**Language:** {dataset.language}")
                st.write(f"**Uploaded:** {dataset.uploaded_at}")
    
                files = get_dataset_files(dataset.id)

                st.write("---")

                for file in files:

                    col1, col2 = st.columns([8, 1])

                    with col1:
                        st.write(f"🎵 {file.original_filename}")

                    with col2:
                        if st.button("🗑", key=f"delete_{file.id}"):
                            delete_audio(file.id)
                            st.rerun()

    st.divider()

    if st.button("← Back"):
        st.session_state.admin_page = "dashboard"
        st.rerun()
        

# =====================================================
# Assignments
# =====================================================
def assignments():

    st.title("📂 Assignments")

    audio_files = get_unassigned_audio()
    annotators = get_annotators()

    if audio_files and annotators:

        with st.form("assign_audio"):

            audio = st.selectbox(
                "Audio File",
                audio_files,
                format_func=lambda x: x.original_filename
            )

            annotator = st.selectbox(
                "Annotator",
                annotators,
                format_func=lambda x: x.username
            )

            submitted = st.form_submit_button("Assign")

        if submitted:

            if assign_audio(audio.id, annotator.id):

                st.success("Assigned successfully.")

                st.rerun()

            else:

                st.error("Assignment failed.")

    elif not audio_files:

        st.info("No unassigned audio available.")

    elif not annotators:

        st.info("No annotators available.")

    st.divider()

    st.subheader("Current Assignments")

    assignments = get_assignments()

    if not assignments:

        st.info("No assignments found.")

    else:

        for audio in assignments:

            with st.expander(audio.original_filename):

                st.write(f"**Language:** {audio.language}")
                st.write(f"**Assigned To:** {audio.assignee.username}")
                st.write(f"**Status:** {audio.status.value}")

                if st.button(
                    "Remove Assignment",
                    key=f"remove_{audio.id}"
                ):

                    unassign_audio(audio.id)

                    st.success("Assignment removed.")

                    st.rerun()

    st.divider()

    if st.button("← Back"):

        st.session_state.admin_page = "dashboard"

        st.rerun()


# =====================================================
# Analytics
# =====================================================
def analytics():

    st.title("📊 Analytics")

    st.info("Coming Soon")

    if st.button("← Back"):

        st.session_state.admin_page = "dashboard"

        st.rerun()


# =====================================================
# Entry
# =====================================================
def show():

    if st.session_state.user.role != UserRole.ADMIN:

        st.error("Access Denied")

        st.stop()

    page = st.session_state.setdefault(
        "admin_page",
        "dashboard"
    )

    pages = {
        "dashboard": dashboard,
        "users": users,
        "audio": audio,
        "assignments": assignments,
        "analytics": analytics,
    }

    pages.get(page, dashboard)()