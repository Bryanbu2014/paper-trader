import pandas as pd
import streamlit as st
import yfinance as yf


def render_dashboard(portfolio):
    # 1. We run the live price math FIRST so we know your total market value
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

    # 2. Now we draw the Performance Overview using the math we just did
    with st.container(border=True):
        st.subheader("Performance Overview")

        history_df = st.session_state.history
        total_trades = len(history_df) if not history_df.empty else 0

        if total_trades > 0:
            unique_tickers = history_df["Ticker"].nunique()
            # Calculate exactly how much cash has moved in and out of your portfolio
            total_buys = history_df[history_df["Action"] == "BUY"]["Total"].sum()
            total_sells = history_df[history_df["Action"] == "SELL"]["Total"].sum()
        else:
            unique_tickers = 0
            total_buys = 0.0
            total_sells = 0.0

        # Current total account value (Cash + Stock Value)
        current_total_value = st.session_state.balance + total_market_value

        # The ultimate P/L formula that ignores starting capital entirely!
        total_pnl = total_market_value - total_buys + total_sells

        # Fix the color bug: Put the minus sign BEFORE the dollar sign
        if total_pnl >= 0:
            pnl_delta_str = f"${total_pnl:,.2f}"
        else:
            pnl_delta_str = f"-${abs(total_pnl):,.2f}"

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Available Cash", f"${st.session_state.balance:,.2f}")
        col2.metric("Net Worth", f"${current_total_value:,.2f}", delta=pnl_delta_str)
        col3.metric("Total Trades", total_trades)
        col4.metric("Assets Traded", unique_tickers)

    # 3. Finally, we draw the Current Holdings table
    with st.container(border=True):
        st.subheader("Current Holdings")

        if portfolio.empty:
            st.info(
                "You don't own any stocks right now. Head over to the Market Terminal to buy some!"
            )
        else:
            holdings_df = pd.DataFrame(holdings_data)

            holdings_df = holdings_df.sort_values(by="Ticker")

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

            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Stock Amount": st.column_config.NumberColumn("Stock Amount"),
                },
            )
