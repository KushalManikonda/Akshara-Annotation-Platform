from datetime import datetime

import streamlit as st

from database.database import SessionLocal
from database.models import User


def logout():

    if "user" in st.session_state:

        db = SessionLocal()

        try:

            user = (
                db.query(User)
                .filter(User.id == st.session_state.user.id)
                .first()
            )

            if user:
                user.last_seen = datetime.utcnow()
                db.commit()

        finally:
            db.close()

    keys = list(st.session_state.keys())

    for key in keys:
        del st.session_state[key]

    st.rerun()