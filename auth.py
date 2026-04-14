import streamlit as st


def check_password():
    """Returns True if the user is logged in, False otherwise."""

    USER_ACCOUNTS = st.secrets["passwords"]

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""

    # If they are already logged in, just say True
    if st.session_state.logged_in:
        return True

    # If not, show the login box
    with st.container(border=True):
        st.title("Restricted Access")
        st.write("Please log in to your personal trading account.")

        with st.form("login_form", border=False):
            input_user = st.text_input("Username").lower()
            input_pass = st.text_input("Password", type="password")
            submit_button = st.form_submit_button(
                "Log In", type="primary", use_container_width=True
            )

            if submit_button:
                if (
                    input_user in USER_ACCOUNTS
                    and USER_ACCOUNTS[input_user] == input_pass
                ):
                    st.session_state.logged_in = True
                    st.session_state.username = input_user
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")

    with st.expander("Request Access"):
        st.write(
            "This trading terminal is currently in **Private Beta**. Want to start your own paper trading journey?"
        )

        col1, col2 = st.columns(2)
        with col1:
            st.link_button(
                "📧 Email Me",
                "mailto:bubryanwb@gmail.com",
                use_container_width=True,
            )
        with col2:
            st.link_button(
                "🔗 LinkedIn",
                "https://www.linkedin.com/in/bryanbuwb/",
                use_container_width=True,
            )

        st.markdown("""
            **How to get an account:**
            1. Send me a message with your preferred **Username**.
            2. I will set up your credentials and provide you with a password.
            
            ---
            * **Note:** Once you have access, your portfolio and trade history will be saved exclusively to your account name.
            * **Note:** You are not allowed to change your password.
            """)

    return False  # Return false if they haven't logged in yet
