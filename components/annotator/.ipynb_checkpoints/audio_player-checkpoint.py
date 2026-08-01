import streamlit as st


def render(audio):

    st.subheader("🎧 Audio Player")

    st.audio(audio.file_path)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.caption(f"Language : {audio.language}")

    with c2:
        st.caption(f"Status : {audio.status.value}")

    with c3:
        st.caption(f"Duration : {audio.duration:.2f} sec")

    with c4:
        st.caption(audio.original_filename)