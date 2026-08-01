import streamlit as st


def render(annotation):

    return st.text_area(
        "Transcript",
        value=annotation.transcript or "",
        height=400
    )