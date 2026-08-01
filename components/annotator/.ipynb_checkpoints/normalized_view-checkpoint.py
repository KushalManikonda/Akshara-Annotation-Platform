import streamlit as st


def render(normalized_text: str):

    st.subheader("Normalized Transcript")

    st.text_area(
        label="",
        value=normalized_text,
        height=400,
        disabled=True,
        key="normalized_transcript"
    )