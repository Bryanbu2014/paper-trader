import pandas as pd
import streamlit as st


def render_journal():
    with st.container(border=True):
        st.subheader("Transaction Log")

        if not st.session_state.history.empty:
            display_df = st.session_state.history.copy()

            def format_cash_flow(row):
                val = row["Total"]
                if row["Action"] == "BUY":
                    return f"-${val:,.2f}"
                else:
                    return f"+${val:,.2f}"

            display_df["Total"] = display_df.apply(format_cash_flow, axis=1)

            display_df["Price"] = display_df["Price"].apply(lambda x: f"${x:,.2f}")

            display_df = display_df.iloc[::-1]

            def color_trade(val):
                if isinstance(val, str):
                    if val.startswith("+"):
                        return "color: #00FF00;"
                    elif val.startswith("-"):
                        return "color: #FF3D00;"
                return ""

            try:
                styled_df = display_df.style.map(color_trade, subset=["Total"])
            except AttributeError:
                styled_df = display_df.style.applymap(color_trade, subset=["Total"])

            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No trades have been recorded yet.")
