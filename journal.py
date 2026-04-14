import streamlit as st


def render_journal():
    with st.container(border=True):
        st.subheader("Transaction Log")
        if not st.session_state.history.empty:
            st.dataframe(
                st.session_state.history.iloc[::-1],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No trades have been recorded yet.")
