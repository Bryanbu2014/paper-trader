import pandas as pd
import streamlit as st


def render_dashboard():
    with st.container(border=True):
        st.subheader("Performance Overview")

        history_df = st.session_state.history
        total_trades = len(history_df) if not history_df.empty else 0

        if total_trades > 0:
            unique_tickers = history_df["Ticker"].nunique()
        else:
            unique_tickers = 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Available Cash", f"${st.session_state.balance:,.2f}")
        col2.metric("Total Trades", total_trades)
        col3.metric("Assets Traded", unique_tickers)

    with st.container(border=True):
        st.subheader("Transaction Log")

        if total_trades > 0:
            st.dataframe(
                history_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                    "Total": st.column_config.NumberColumn("Total", format="$%.2f"),
                    "Action": st.column_config.TextColumn("Action"),
                },
            )
        else:
            st.info("No trades have been recorded yet.")
