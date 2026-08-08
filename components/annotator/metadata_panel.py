import streamlit as st
import json

def render(task):
    """
    Displays the contextual metadata (Original Transcript & Translation)
    for the annotator to reference while annotating.
    """
    st.subheader("📄 Context")
    
    with st.expander("Original Transcript", expanded=True):
        if task.original_transcript:
            try:
                parsed = json.loads(task.original_transcript)
                st.write(json.dumps(parsed, ensure_ascii=False, indent=2))
            except Exception:
                st.write(task.original_transcript)
        else:
            st.write("*(No original transcript available)*")
        
    with st.expander("English Translation", expanded=True):
        if task.english_translation:
            try:
                parsed = json.loads(task.english_translation)
                st.write(json.dumps(parsed, ensure_ascii=False, indent=2))
            except Exception:
                st.write(task.english_translation)
        else:
            st.write("*(No english translation available)*")
        
    if task.metadata_json:
        try:
            extra = json.loads(task.metadata_json)
            if extra:
                with st.expander("Additional Metadata", expanded=False):
                    st.write(json.dumps(extra, ensure_ascii=False, indent=2))
        except Exception:
            pass
