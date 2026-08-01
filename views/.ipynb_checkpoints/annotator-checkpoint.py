import streamlit as st

from utils.logout import logout

from components.annotator.audio_player import render as audio_player
from components.annotator.navigation import render as navigation
from components.annotator.transcript_editor import render as transcript_editor
from components.annotator.normalized_view import render as normalized_view
from components.annotator.validation_panel import render as validation_panel
from components.annotator.rsml_toolbar import render as rsml_toolbar
from components.annotator.footer import render as footer

from services.annotation_service import (
    get_tasks,
    get_annotation,
    save_annotation,
    submit_annotation,
    process_transcript,
)

def show():

    user = st.session_state.user

    if "selected_task" not in st.session_state:
        st.session_state.selected_task = None

    col1, col2 = st.columns([8, 1])

    with col1:
        st.title("Annotator Dashboard")

    with col2:
        if st.button("Logout", use_container_width=True):
            logout()

    tasks = get_tasks(user.id)

    ###########################################################
    # TASK QUEUE
    ###########################################################

    if st.session_state.selected_task is None:

        st.subheader("My Tasks")

        if len(tasks) == 0:
            st.info("No assigned audio.")
            return

        for task in tasks:

            c1, c2 = st.columns([6, 1])

            with c1:

                st.write(f"**{task.original_filename}**")
                st.caption(task.language)
                st.caption(task.status.value)

            with c2:

                if st.button(
                    "Open",
                    key=task.id,
                    use_container_width=True,
                ):

                    st.session_state.selected_task = task.id
                    st.rerun()

            st.divider()

        return

    ###########################################################
    # WORKSPACE
    ###########################################################

    task = next(
        (
            x
            for x in tasks
            if x.id == st.session_state.selected_task
        ),
        None,
    )

    if task is None:

        st.session_state.selected_task = None
        st.rerun()

    annotation = get_annotation(task.id, user.id)

    previous_clicked, next_clicked = navigation()

    audio_player(task)

    st.divider()

    left, right = st.columns([3, 2])

    with left:

        transcript = transcript_editor(annotation)

        rsml_toolbar()

    # Process the transcript through the RSML pipeline
    result = process_transcript(transcript)

    normalized_text = result["normalized"]
    messages = result["messages"]

    with right:

        normalized_view(normalized_text)

        validation_panel(messages)

    st.divider()

    has_errors = any(
        message.level == "ERROR"
        for message in messages
    )

    save, validate, submit = footer(has_errors)

    if save:

        save_annotation(
            annotation.id,
            transcript,
            annotation.rsml_content or "",
        )

        st.success("Draft saved.")

    if validate:

        st.info("Validation engine coming next.")

    if submit:

        submit_annotation(annotation.id)

        st.success("Annotation submitted.")

        st.session_state.selected_task = None

        st.rerun()