from datetime import datetime
import pandas as pd
import streamlit as st
import yfinance as yf


def render_dashboard(portfolio, supabase):

    if "history_limit" not in st.session_state:
        st.session_state.history_limit = 10

    holdings_data = []
    total_market_value = 0.0

    if not portfolio.empty:
        with st.spinner("Fetching live market prices..."):
            for index, row in portfolio.iterrows():
                ticker = row["Ticker"]
                qty = row["Quantity"]
                avg_price = float(row["Avg Price"].replace("$", "").replace(",", ""))

                try:
                    stock = yf.Ticker(ticker)
                    live_price = stock.history(
                        period="1d", interval="1m", prepost=True
                    )["Close"].iloc[-1]

                    total_value = qty * live_price
                    total_market_value += total_value

                    total_cost = qty * avg_price
                    profit = total_value - total_cost

                    if profit >= 0:
                        worth_str = f"${total_value:,.2f} (+${profit:,.2f})"
                    else:
                        worth_str = f"${total_value:,.2f} (-${abs(profit):,.2f})"

                    holdings_data.append(
                        {
                            "Ticker": ticker,
                            "Stock Amount": qty,
                            "Buy-in Price": row["Avg Price"],
                            "Live Price": f"${live_price:,.2f}",
                            "Total Worth": worth_str,
                        }
                    )
                except:
                    holdings_data.append(
                        {
                            "Ticker": ticker,
                            "Stock Amount": qty,
                            "Buy-in Price": row["Avg Price"],
                            "Live Price": "Error",
                            "Total Worth": "Error",
                        }
                    )

    current_total_value = st.session_state.balance + total_market_value

    today = datetime.now().date().isoformat()
    username = st.session_state.username

    check = (
        supabase.table("net_worth_history")
        .select("id")
        .eq("username", username)
        .eq("timestamp", today)
        .execute()
    )

    if check.data:

        row_id = check.data[0]["id"]
        supabase.table("net_worth_history").update(
            {"net_worth": current_total_value}
        ).eq("id", row_id).execute()
    else:

        supabase.table("net_worth_history").insert(
            {"username": username, "net_worth": current_total_value, "timestamp": today}
        ).execute()

    with st.container(border=True):
        st.subheader("Performance Overview")

        history_df = st.session_state.history
        total_trades = len(history_df) if not history_df.empty else 0

        if total_trades > 0:
            unique_tickers = history_df["Ticker"].nunique()
            total_buys = history_df[history_df["Action"] == "BUY"]["Total"].sum()
            total_sells = history_df[history_df["Action"] == "SELL"]["Total"].sum()
        else:
            unique_tickers = 0
            total_buys = 0.0
            total_sells = 0.0

        total_pnl = total_market_value - total_buys + total_sells

        if total_pnl >= 0:
            pnl_delta_str = f"${total_pnl:,.2f}"
        else:
            pnl_delta_str = f"-${abs(total_pnl):,.2f}"

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Available Cash", f"${st.session_state.balance:,.2f}")
        col2.metric("Net Worth", f"${current_total_value:,.2f}", delta=pnl_delta_str)
        col3.metric("Total Trades", total_trades)
        col4.metric("Assets Traded", unique_tickers)

    with st.container(border=True):
        st.subheader("Current Holdings")

        if portfolio.empty:
            st.info(
                "You don't own any stocks right now. Head over to the Market Terminal to buy some!"
            )
        else:
            holdings_df = pd.DataFrame(holdings_data).sort_values(by="Ticker")

            def color_profit(val):
                if isinstance(val, str):
                    if "(+" in val:
                        return "color: #00FF00;"
                    elif "(-" in val:
                        return "color: #FF3D00;"
                return ""

            try:
                styled_df = holdings_df.style.map(color_profit, subset=["Total Worth"])
            except AttributeError:
                styled_df = holdings_df.style.applymap(
                    color_profit, subset=["Total Worth"]
                )

            st.dataframe(styled_df, use_container_width=True, hide_index=True)

    with st.container(border=True):
        st.subheader("Daily Performance History")

        history_res = (
            supabase.table("net_worth_history")
            .select("timestamp, net_worth")
            .eq("username", username)
            .execute()
        )

        if history_res.data:
            hist_df = pd.DataFrame(history_res.data)

            hist_df = hist_df.sort_values("timestamp")

            hist_df["Daily Gain/Loss"] = hist_df["net_worth"].diff()

            starting_capital = 100000.0
            hist_df["Daily Gain/Loss"] = hist_df["Daily Gain/Loss"].fillna(
                hist_df["net_worth"] - starting_capital
            )

            hist_df["Net Worth"] = hist_df["net_worth"].apply(lambda x: f"${x:,.2f}")

            def format_pnl(val):
                if val > 0:
                    return f"+${val:,.2f}"
                elif val < 0:
                    return f"-${abs(val):,.2f}"
                return "$0.00"

            hist_df["Daily Gain/Loss"] = hist_df["Daily Gain/Loss"].apply(format_pnl)

            hist_df = hist_df.sort_values("timestamp", ascending=False)

            total_rows = len(hist_df)

            display_df = hist_df[["timestamp", "Net Worth", "Daily Gain/Loss"]].rename(
                columns={"timestamp": "Date"}
            )

            display_df = display_df.head(st.session_state.history_limit)

            def color_daily_pnl(val):
                if "+" in val:
                    return "color: #00FF00;"
                elif "-" in val:
                    return "color: #FF3D00;"
                return ""

            try:
                styled_history = display_df.style.map(
                    color_daily_pnl, subset=["Daily Gain/Loss"]
                )
            except AttributeError:
                styled_history = display_df.style.applymap(
                    color_daily_pnl, subset=["Daily Gain/Loss"]
                )

            st.dataframe(styled_history, use_container_width=True, hide_index=True)
            if total_rows > st.session_state.history_limit:
                col1, col2, col3 = st.columns([2, 1, 2])

                with col2:
                    if total_rows > st.session_state.history_limit:
                        if st.button("Load 10 More Rows", use_container_width=True):
                            st.session_state.history_limit += 10
                            st.rerun()
        else:
            st.info("No daily history recorded yet. Check back tomorrow!")
