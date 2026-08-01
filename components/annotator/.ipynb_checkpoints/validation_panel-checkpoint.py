import streamlit as st


def render(messages):

    st.subheader("Validation")

    if not messages:
        st.success("✅ No validation errors.")
        return

    errors = [m for m in messages if m.level == "ERROR"]
    warnings = [m for m in messages if m.level == "WARNING"]

    if errors:
        st.error(f"Errors ({len(errors)})")

        for error in errors:
            st.write(f"• {error.message}")

    if warnings:
        st.warning(f"Warnings ({len(warnings)})")

        for warning in warnings:
            st.write(f"• {warning.message}")