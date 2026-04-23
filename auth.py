import uuid

import streamlit as st
from streamlit_local_storage import LocalStorage

import database

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
        db_session_id = database.get_session_id(st.session_state.username)
        if st.session_state.get("session_id") == db_session_id:
            return True
        else:
            st.session_state.logged_in = False
            st.session_state.username = ""
            if "session_id" in st.session_state:
                del st.session_state.session_id
            st.warning("You have been logged out because your account was accessed from another device.")

    login_screen = st.empty()

    with login_screen.container():

        st.markdown(
            """
            <div style='text-align: center; margin-bottom: 30px;'>
                <h1 style='font-size: 80px; margin-bottom: 5px;' class='main-logo'>
                    Paper Trading Lab</br><span class='version-badge'>v1.3.0</span>
                </h1>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            st.title("⛔ Restricted Access")
            st.write("Please log in to your personal trading account.")

            local_storage = LocalStorage()
            saved_user = local_storage.getItem("remembered_username")
            default_user = saved_user if saved_user else ""

            with st.form("login_form", border=False):
                input_user = st.text_input("Username", value=default_user).lower()
                input_pass = st.text_input("Password", type="password")
                remember_me = st.checkbox("Remember me", value=bool(default_user))
                submit_button = st.form_submit_button(
                    "Log In", type="primary", use_container_width=True
                )

                if submit_button:
                    if (
                        input_user in USER_ACCOUNTS
                        and USER_ACCOUNTS[input_user] == input_pass
                    ):
                        if remember_me:
                            local_storage.setItem("remembered_username", input_user)
                        else:
                            local_storage.setItem("remembered_username", "")

                        st.session_state.logged_in = True
                        st.session_state.username = input_user
                        
                        new_session_id = str(uuid.uuid4())
                        st.session_state.session_id = new_session_id
                        database.update_session_id(input_user, new_session_id)
                        
                        st.rerun()
                    else:
                        st.error("Incorrect username or password.")

        with st.expander("🚀 What's New?"):
            with st.expander("v1.4.0"):
                st.info("Released: April 24, 2026")
                st.markdown(
                    """
                    ### New Features ✨
                    - Integrated a tabbed layout in the Market Terminal for market research and analytics
                    """
                )
            with st.expander("v1.3.0"):
                st.info("Released: April 23, 2026")
                st.markdown(
                    """
                    ### Security & Authentication 🛡️
                    - Implemented single-device session to enhance account security
                    - Added automatic logout when an account is accessed from another device
                    - Ensured all authentication remain in session-based and expire upon browser closure
                    
                    ### UI/UX Improvements 💄
                    - Added a 'Remember me' feature to auto-fill username for quicker logins
                    """
                )
            with st.expander("v1.2.0"):
                st.info("Released: April 22, 2026")
                st.markdown(
                    """
                    ### CI Integration 🔥
                    - Set up a CI task to ping the Streamlit app periodically to prevent shutdown

                    ### New Features ✨
                    - Integrated a real-time clock in the sidebar that automatically syncs with the user's current location
                    - The app now automatically detects the user's browser's timezone to ensure all data is relevant to the user
                    - Added Unrealized and Realized Profit/Loss (P/L) tracking to the Performance Overview panel
                    - Included a new daily breakdown of Realized Gain/Loss in the Daily Performance History panel

                    ### Bug Fixes 🛠️
                    - Fixed a bug where trade success messages ("Bought/Sold") disappeared instantly
                    - Corrected the 2-hour discrepancy between the server (UTC) and local time (CEST)
                    - Fixed a math bug where the avg buy-in price for stocks was incorrect because it included old, sold shares

                    ### UI/UX Improvements 💄
                    - Removed distracting anchor links from headers
                    - Upgraded the version badge with a smooth animated background
                    """
                )
            with st.expander("v1.1.0"):
                st.info("Released: April 16, 2026")
                st.markdown(
                    """
                    ### New Features ✨
                    - Introduced a dedicated Settings menu with a full account reset functionality
                    - Implemented daily performance history to track daily gain/loss
                    - Included transaction fee for each buy/sell transaction
                    - Created inline confirmation for item deletion to prevent accidental clicks
                    - Implemented __Settings__ page to allow user customized settings
                    
                    ### Performance & Architecture 🚀
                    - Centralized live market data into a 'Single Source of Truth' to perfectly sync prices across all tabs
                    - Optimized API requests with batch downloading to drastically improve app speed and prevent IP bans
                    - Implemented independent UI fragments in the Market Terminal to prevent full-page reloads
                    - Built a fail-safe data retrieval mechanism to guarantee uninterrupted live price feeds
                    
                    ### UI/UX Improvements 💄
                    - Applied custom CSS styling for a cleaner, more modern interface
                    - Added dynamic color-coding to instantly distinguish profit (green) and loss (red)
                    - Reorganized the Market Terminal layout for a much smoother trading experience
                    - Standardized all financial metrics and portfolio values to a clean, 2-decimal-place format
                    - Moved version badge one line below the title
                    - Included light mode
                    - Swapped __What's New?__ view with __Request Access__ view on login page
                    """
                )
            with st.expander("v1.0.0"):
                st.info("Released: April 14, 2026")
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

    return False
