from datetime import datetime, timezone

import pandas as pd
import pytz
import streamlit as st
import yfinance as yf

import database


@st.fragment
def render_watchlist():
    with st.container(border=True):
        st.subheader("Live Watchlist")
        wl_display_data = []

        if st.session_state.watchlist:
            for t in st.session_state.watchlist:

                price = st.session_state.live_prices.get(t)

                if price is not None:
                    wl_display_data.append(
                        {"Ticker": t, "Live Price": f"${price:,.2f}"}
                    )
                else:
                    wl_display_data.append(
                        {"Ticker": t, "Live Price": "Error fetching"}
                    )

        if wl_display_data:
            st.dataframe(
                pd.DataFrame(wl_display_data),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.write("*Watchlist is empty.*")

    with st.container(border=True):
        st.subheader("Manage List")
        with st.form("add_stock_form", border=False):
            add_col1, add_col2 = st.columns([2, 1], vertical_alignment="bottom")

            with add_col1:
                new_ticker = st.text_input("Ticker to Add", key="add_t").upper()
            with add_col2:
                submit_add = st.form_submit_button("➕ Add", use_container_width=True)

            if submit_add:
                if new_ticker and new_ticker not in st.session_state.watchlist:
                    st.session_state.watchlist.append(new_ticker)
                    st.session_state.watchlist.sort()
                    database.update_watchlist(
                        st.session_state.username, st.session_state.watchlist
                    )
                    st.rerun()

        if st.session_state.watchlist:
            rem_col1, rem_col2 = st.columns([2, 1], vertical_alignment="bottom")
            with rem_col1:
                ticker_to_remove = st.selectbox(
                    "Ticker to Remove", st.session_state.watchlist
                )
            with rem_col2:
                if st.button("❌ Drop", use_container_width=True):
                    st.session_state.watchlist.remove(ticker_to_remove)
                    database.update_watchlist(
                        st.session_state.username, st.session_state.watchlist
                    )
                    st.rerun()

            if "clear_watchlist_warning" not in st.session_state:
                st.session_state.clear_watchlist_warning = False

            def show_warning():
                st.session_state.clear_watchlist_warning = True

            def hide_warning():
                st.session_state.clear_watchlist_warning = False

            if not st.session_state.clear_watchlist_warning:
                st.button(
                    "🗑️ Clear Entire Watchlist",
                    use_container_width=True,
                    type="primary",
                    on_click=show_warning,
                )
            else:
                st.error(
                    "Are you sure you want to delete every ticker from your watchlist?"
                )
                c1, c2 = st.columns(2)

                c1.button("Cancel", use_container_width=True, on_click=hide_warning)

                if c2.button("Yes, Clear It", type="primary", use_container_width=True):
                    st.session_state.watchlist = []
                    database.update_watchlist(
                        st.session_state.username, st.session_state.watchlist
                    )
                    st.session_state.clear_watchlist_warning = False
                    st.rerun()


@st.fragment
def render_trade_panel(portfolio):
    with st.container(border=True):
        st.subheader("Target Quote")
        ticker = (
            st.text_input("Enter Target Ticker (e.g., TSLA, AAPL)", "")
            .upper()
            .replace(" ", "")
        )
        current_price = 0
        if ticker:
            try:
                stock = yf.Ticker(ticker)
                price_data = stock.history(period="1d", interval="1m", prepost=True)
                if not price_data.empty:
                    raw_current = price_data["Close"].iloc[-1]
                    current_price = round(float(raw_current), 2)

                    st.metric(
                        label=f"Current {ticker} Price",
                        value=f"${current_price:,.2f}",
                    )
                else:
                    st.warning("No data found right now.")
            except Exception as e:
                st.error("Could not fetch data. Check the ticker symbol.")

    with st.container(border=True):
        st.subheader("Execute Trade")
        if current_price > 0:
            c1, c2 = st.columns([1, 1], vertical_alignment="center")
            with c1:
                qty = st.number_input("Quantity to Trade", min_value=1, step=1)
                fee = st.session_state.transaction_fee
                st.write(f"**Transaction Fee:** ${fee:,.2f}")
            with c1:
                total = qty * current_price
                st.metric(label="Total Before Transaction Fee", value=f"${total:,.2f}")

            shares_owned = 0
            buy_in_price = "$0.00"

            if not portfolio.empty and ticker in portfolio["Ticker"].values:
                stock_row = portfolio.loc[portfolio["Ticker"] == ticker]
                shares_owned = stock_row["Quantity"].iloc[0]
                buy_in_price = stock_row["Avg Price"].iloc[0]

            if shares_owned > 0:
                st.info(
                    f"💼 You own **{shares_owned} shares** at a buy-in price of **{buy_in_price}**"
                )
            else:
                st.write(f"You currently own: **0 shares**")

            btn_buy, btn_sell = st.columns(2)

            user_tz_name = st.context.timezone or "UTC"
            user_tz = pytz.timezone(user_tz_name)
            now_utc = datetime.now(timezone.utc)
            local_now = now_utc.astimezone(user_tz)
            timestamp_str = local_now.strftime("%Y-%m-%d %H:%M:%S")

            if btn_buy.button("🟢 BUY SHARES", use_container_width=True):
                total_cost = total + fee

                if st.session_state.balance >= total_cost:
                    st.session_state.balance -= total_cost
                    new_trade = {
                        "Timestamp": timestamp_str,
                        "Ticker": ticker,
                        "Action": "BUY",
                        "Quantity": qty,
                        "Price": current_price,
                        "Total": round(total_cost, 2),
                    }
                    st.session_state.history = pd.concat(
                        [st.session_state.history, pd.DataFrame([new_trade])],
                        ignore_index=True,
                    )

                    database.update_balance(
                        st.session_state.username, st.session_state.balance
                    )
                    database.add_trade(st.session_state.username, new_trade)

                    st.session_state.trade_msg = (
                        f"✅ Successfully bought {qty} shares of {ticker}!"
                    )
                    st.rerun()
                else:
                    st.error("Not enough cash!")

            if btn_sell.button("🔴 SELL SHARES", use_container_width=True):
                if shares_owned >= qty:
                    total_revenue = total - fee
                    st.session_state.balance += total_revenue
                    new_trade = {
                        "Timestamp": timestamp_str,
                        "Ticker": ticker,
                        "Action": "SELL",
                        "Quantity": qty,
                        "Price": current_price,
                        "Total": round(total_revenue, 2),
                    }
                    st.session_state.history = pd.concat(
                        [st.session_state.history, pd.DataFrame([new_trade])],
                        ignore_index=True,
                    )

                    database.update_balance(
                        st.session_state.username, st.session_state.balance
                    )
                    database.add_trade(st.session_state.username, new_trade)

                    st.session_state.trade_msg = (
                        f"✅ Successfully sold {qty} shares of {ticker}!"
                    )
                    st.rerun()
                else:
                    st.error(f"You only own {shares_owned} shares.")

            if "trade_msg" in st.session_state:
                st.success(st.session_state.trade_msg)
                del st.session_state.trade_msg

        else:
            st.info("Enter a valid target ticker above to enable trading.")


def render_terminal(portfolio):

    col_watch, col_trade = st.columns([1, 2], gap="large")

    with col_watch:
        render_watchlist()

    with col_trade:
        render_trade_panel(portfolio)
