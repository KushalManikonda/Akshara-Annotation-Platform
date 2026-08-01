import streamlit as st


def render(has_errors: bool):

    c1, c2, c3 = st.columns(3)

    save = c1.button(
        "💾 Save Draft",
        use_container_width=True
    )

    validate = c2.button(
        "✔ Validate",
        use_container_width=True
    )

    submit = c3.button(
        "📤 Submit",
        use_container_width=True,
        disabled=has_errors
    )

    return save, validate, submit