import os
import streamlit as st

from services.reviewer_service import (
    get_submitted_annotations,
    add_comment,
    approve
)

from utils.logout import logout


def show():

    reviewer = st.session_state.user

    if "selected_review" not in st.session_state:
        st.session_state.selected_review = None

    col1, col2 = st.columns([8, 1])

    with col1:
        st.title("Reviewer Dashboard")

    with col2:
        if st.button("Logout", use_container_width=True):
            logout()

    reviews = get_submitted_annotations()

    if st.session_state.selected_review is None:

        st.subheader("Submitted Annotations")

        st.caption(f"Reviewer : {reviewer.username}")
        st.caption(f"Pending Reviews : {len(reviews)}")

        if len(reviews) == 0:
            st.info("No submitted annotations.")
            return

        for annotation in reviews:

            audio = annotation.audio

            with st.container():

                c1, c2 = st.columns([6, 1])

                with c1:
                    st.write(f"**{audio.original_filename}**")
                    st.caption(f"Language : {audio.language}")
                    st.caption(f"Annotator : {annotation.annotator.username}")
                    st.caption(f"Status : {annotation.state.value}")

                with c2:
                    if st.button("Open", key=annotation.id):
                        st.session_state.selected_review = annotation.id
                        st.rerun()

            st.divider()

        return

    annotation = next(
        (
            x
            for x in reviews
            if x.id == st.session_state.selected_review
        ),
        None,
    )

    if annotation is None:
        st.session_state.selected_review = None
        st.rerun()

    audio = annotation.audio

    st.header(audio.original_filename)

    c1, c2 = st.columns(2)

    with c1:
        st.write(f"**Language:** {audio.language}")

    with c2:
        st.write(f"**Annotator:** {annotation.annotator.username}")

    if os.path.exists(audio.file_path):
        st.audio(audio.file_path)

    st.divider()

    transcript = st.text_area(
        "Transcript",
        value=annotation.transcript or "",
        height=250,
        disabled=True,
    )

    rsml = st.text_area(
        "RSML",
        value=annotation.rsml_content or "",
        height=250,
        disabled=True,
    )

    comment = st.text_area(
        "Reviewer Comment",
        height=150,
        placeholder="Enter review comments if returning..."
    )

    st.divider()

    b1, b2, b3 = st.columns(3)

    with b1:

        if st.button(
            "Approve",
            use_container_width=True
        ):

            approve(
                annotation.id,
                reviewer.id
            )

            st.success("Annotation approved.")

            st.session_state.selected_review = None

            st.rerun()

    with b2:

        if st.button(
            "Return",
            use_container_width=True
        ):

            if comment.strip() == "":

                st.error("Reviewer comment is required.")

            else:

                add_comment(
                    annotation.id,
                    reviewer.id,
                    comment
                )

                st.success("Returned to annotator.")

                st.session_state.selected_review = None

                st.rerun()

    with b3:

        if st.button(
            "Back",
            use_container_width=True
        ):

            st.session_state.selected_review = None

            st.rerun()