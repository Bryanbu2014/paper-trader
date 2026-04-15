import streamlit as st


def check_password():
    """Returns True if the user is logged in, False otherwise."""

    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    USER_ACCOUNTS = st.secrets["passwords"]

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""

    if st.session_state.logged_in:
        return True

    login_screen = st.empty()

    with login_screen.container():

        st.markdown(
            """
            <div style='text-align: center; margin-bottom: 30px;'>
                <h1 style='font-size: 80px; margin-bottom: 5px;' class='main-logo'>
                    Paper Trading Lab</br><span class='version-badge'>v1.0.0</span>
                </h1>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Login Form Container
        with st.container(border=True):
            st.title("⛔ Restricted Access")
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

        # Request Access Toggle
        with st.expander("🔑 Request Access"):
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

            st.markdown(
                """
                **How to get an account:**
                1. Send me a message with your preferred **Username**.
                2. I will set up your credentials and provide you with a password.
                
                ---
                * **Note:** Once you have access, your portfolio and trade history will be saved exclusively to your account name.
                * **Note:** You are not allowed to change your password.
                """
            )

        with st.expander("🚀 What's New?"):
            with st.expander("v1.0.1"):
                st.markdown(
                    """
                    ### New Features ✨
                    - Implemented daily performance history to track daily gain/loss
                    - Included transaction fee for each buy/sell transaction
                    ### UI/UX Improvements 💄
                    - Moved version badge one line below the title

                    """
                )
            with st.expander("v1.0.0"):
                st.markdown(
                    """
                    - Deployed the app to the internet
                    - Connected the app to a database
                    - Added a login screen for only authorized users
                    - Built the screen for buying and selling stocks
                    - Created dashboard
                    - Added a simple history list
                    """
                )

    return False
