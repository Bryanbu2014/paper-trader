from datetime import datetime

import pandas as pd
import streamlit as st

import database


def calculate_realized_pnl(history_df):
    """
    Looks at the entire trade history to calculate locked-in cash profits.
    Returns the total realized PnL AND a dictionary breaking it down by day.
    """
    total_realized_pnl = 0.0
    daily_realized_pnl = {}
    inventory = {}

    if history_df is None or history_df.empty:
        return 0.0, {}

    sorted_history = history_df.sort_values(by="Timestamp")

    for _, row in sorted_history.iterrows():
        t = row["Ticker"]
        action = row["Action"]
        qty = row["Quantity"]
        total = row["Total"]

        date_str = str(row["Timestamp"])[:10]

        if date_str not in daily_realized_pnl:
            daily_realized_pnl[date_str] = 0.0

        if t not in inventory:
            inventory[t] = {"qty": 0, "total_cost": 0.0}

        if action == "BUY":
            inventory[t]["qty"] += qty
            inventory[t]["total_cost"] += total

        elif action == "SELL":
            if inventory[t]["qty"] > 0:

                avg_cost = inventory[t]["total_cost"] / inventory[t]["qty"]
                cost_of_sold = avg_cost * qty

                profit = total - cost_of_sold

                total_realized_pnl += profit
                daily_realized_pnl[date_str] += profit

                inventory[t]["qty"] -= qty
                inventory[t]["total_cost"] -= cost_of_sold

    return total_realized_pnl, daily_realized_pnl


def render_dashboard(portfolio):

    if "history_limit" not in st.session_state:
        st.session_state.history_limit = 10

    history_df = st.session_state.history

    total_realized_pnl, daily_realized_pnl = calculate_realized_pnl(history_df)

    holdings_data = []
    total_market_value = 0.0
    total_unrealized_pnl = 0.0

    if not portfolio.empty:
        for index, row in portfolio.iterrows():
            ticker = row["Ticker"]
            qty = row["Quantity"]
            avg_price = row["Raw Price"]

            live_price = st.session_state.live_prices.get(ticker)

            if live_price is not None:
                total_value = qty * live_price
                total_market_value += total_value

                total_cost = qty * avg_price
                unrealized_profit = total_value - total_cost
                total_unrealized_pnl += unrealized_profit

                if unrealized_profit >= 0:
                    unrealized_str = f"+${unrealized_profit:,.2f}"
                else:
                    unrealized_str = f"-${abs(unrealized_profit):,.2f}"

                holdings_data.append(
                    {
                        "Ticker": ticker,
                        "Quantity": qty,
                        "Avg Price": row["Avg Price"],
                        "Live Price": f"${live_price:,.2f}",
                        "Total Value": f"${total_value:,.2f}",
                        "Unrealized P/L": unrealized_str,
                    }
                )
            else:
                holdings_data.append(
                    {
                        "Ticker": ticker,
                        "Quantity": qty,
                        "Avg Price": row["Avg Price"],
                        "Live Price": "Error",
                        "Total Value": "Error",
                        "Unrealized P/L": "Error",
                    }
                )

    current_total_value = st.session_state.balance + total_market_value
    username = st.session_state.username

    database.save_daily_net_worth(username, current_total_value)

    with st.container(border=True):
        st.subheader("Performance Overview")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Net Worth", f"${current_total_value:,.2f}")
        col2.metric("Available Cash", f"${st.session_state.balance:,.2f}")

        formatted_unrealized = (
            f"${total_unrealized_pnl:,.2f}"
            if total_unrealized_pnl >= 0
            else f"-${abs(total_unrealized_pnl):,.2f}"
        )
        formatted_realized = (
            f"${total_realized_pnl:,.2f}"
            if total_realized_pnl >= 0
            else f"-${abs(total_realized_pnl):,.2f}"
        )

        col3.metric("Total Unrealized P/L", formatted_unrealized)
        col4.metric("Total Realized P/L", formatted_realized)

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
                    if val.startswith("+"):
                        return "color: #00FF00;"
                    elif val.startswith("-"):
                        return "color: #FF3D00;"
                return ""

            try:
                styled_df = holdings_df.style.map(
                    color_profit, subset=["Unrealized P/L"]
                )
            except AttributeError:
                styled_df = holdings_df.style.applymap(
                    color_profit, subset=["Unrealized P/L"]
                )

            st.dataframe(styled_df, use_container_width=True, hide_index=True)

    with st.container(border=True):
        st.subheader("Daily Performance History")

        hist_df = database.get_net_worth_history(username)

        if hist_df is not None and not hist_df.empty:

            hist_df = hist_df.sort_values("timestamp")

            hist_df["Daily P/L"] = hist_df["net_worth"].diff()

            total_buys = (
                history_df[history_df["Action"] == "BUY"]["Total"].sum()
                if not history_df.empty
                else 0.0
            )
            total_sells = (
                history_df[history_df["Action"] == "SELL"]["Total"].sum()
                if not history_df.empty
                else 0.0
            )

            dynamic_starting_capital = (
                st.session_state.balance + total_buys - total_sells
            )

            hist_df["Daily P/L"] = hist_df["Daily P/L"].fillna(
                hist_df["net_worth"] - dynamic_starting_capital
            )

            hist_df["Net Worth"] = hist_df["net_worth"].apply(lambda x: f"${x:,.2f}")

            def get_daily_realized(date_val):
                return daily_realized_pnl.get(str(date_val), 0.0)

            hist_df["Realized P/L"] = hist_df["timestamp"].apply(get_daily_realized)

            def format_pnl(val):
                if val > 0:
                    return f"+${val:,.2f}"
                elif val < 0:
                    return f"-${abs(val):,.2f}"
                return "$0.00"

            hist_df["Daily P/L"] = hist_df["Daily P/L"].apply(format_pnl)
            hist_df["Realized P/L"] = hist_df["Realized P/L"].apply(format_pnl)

            hist_df = hist_df.sort_values("timestamp", ascending=False)
            total_rows = len(hist_df)

            display_df = hist_df[
                ["timestamp", "Net Worth", "Daily P/L", "Realized P/L"]
            ].rename(columns={"timestamp": "Date"})
            display_df = display_df.head(st.session_state.history_limit)

            def color_daily_pnl(val):
                if isinstance(val, str):
                    if "+" in val:
                        return "color: #00FF00;"
                    elif "-" in val:
                        return "color: #FF3D00;"
                return ""

            try:

                styled_history = display_df.style.map(
                    color_daily_pnl, subset=["Daily P/L", "Realized P/L"]
                )
            except AttributeError:
                styled_history = display_df.style.applymap(
                    color_daily_pnl, subset=["Daily P/L", "Realized P/L"]
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
