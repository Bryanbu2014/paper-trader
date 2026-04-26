import streamlit as st

import database


@st.dialog("⚙️ Settings")
def render_settings(wipe_account_func):

    st.subheader("Trading Rules")

    new_fee = st.number_input(
        "Transaction Fee ($)",
        min_value=0.0,
        value=float(st.session_state.transaction_fee),
        step=0.5,
        key="new_fee_input",
    )
    
    mho_enabled = st.checkbox(
        "Restrict Trading to Extended US Market Hours (4:00 AM - 8:00 PM ET)",
        value=st.session_state.market_hours_only,
        help="If enabled, you can only execute trades during US pre-market, regular, and after-hours sessions (Mon-Fri)."
    )

    if st.button("Save Settings", use_container_width=True):
        st.session_state.transaction_fee = new_fee
        st.session_state.market_hours_only = mho_enabled
        database.update_settings(st.session_state.username, new_fee, mho_enabled)
        st.rerun()

    st.divider()

    st.subheader("Danger Zone")
    new_capital = st.number_input(
        "Starting Capital for Reset ($)",
        min_value=100.0,
        value=100000.0,
        step=1000.0,
        key="reset_cap",
    )

    if "show_reset_warning" not in st.session_state:
        st.session_state.show_reset_warning = False

    def show_warning():
        st.session_state.show_reset_warning = True

    def hide_warning():
        st.session_state.show_reset_warning = False

    if not st.session_state.show_reset_warning:
        st.button(
            "⚠️ Restart Account",
            type="primary",
            use_container_width=True,
            on_click=show_warning,
        )

    else:
        st.error(
            "Are you absolutely sure? This will delete all your trades and daily history. This cannot be undone."
        )
        c1, c2 = st.columns(2)

        c1.button("Cancel", use_container_width=True, on_click=hide_warning)

        if c2.button("Yes, Wipe Everything", type="primary", use_container_width=True):
            wipe_account_func(new_capital)
            st.session_state.show_reset_warning = False
            st.rerun()
