from datetime import datetime
import pandas as pd
import streamlit as st
import yfinance as yf


@st.dialog("⚠️ Confirm Clear Watchlist")
def confirm_clear_dialog(update_watchlist_func):
    st.error("Are you sure you want to delete every ticker from your watchlist?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

    with col2:
        if st.button("Yes, Clear It", type="primary", use_container_width=True):
            # Wipe the list and update the database
            st.session_state.watchlist = []
            update_watchlist_func(st.session_state.username, st.session_state.watchlist)
            st.rerun()


def render_terminal(portfolio, update_balance, add_trade_to_db, update_watchlist):
    col_watch, col_trade = st.columns([1, 2], gap="large")

    with col_watch:
        with st.container(border=True):
            st.subheader("Live Watchlist")
            wl_display_data = []
            for t in st.session_state.watchlist:
                try:
                    stock = yf.Ticker(t)
                    price = stock.history(period="1d", interval="1m", prepost=True)[
                        "Close"
                    ].iloc[-1]
                    wl_display_data.append(
                        {"Ticker": t, "Live Price": f"${price:,.2f}"}
                    )
                except:
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
                    submit_add = st.form_submit_button(
                        "➕ Add", use_container_width=True
                    )

                if submit_add:
                    if new_ticker and new_ticker not in st.session_state.watchlist:
                        st.session_state.watchlist.append(new_ticker)
                        st.session_state.watchlist.sort()
                        update_watchlist(
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
                        update_watchlist(
                            st.session_state.username, st.session_state.watchlist
                        )
                        st.rerun()

                if st.button(
                    "🗑️ Clear Entire Watchlist", use_container_width=True, type="primary"
                ):
                    confirm_clear_dialog(update_watchlist)

    with col_trade:
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
                        current_price = price_data["Close"].iloc[-1]
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
                    # Added Transaction Fee Input here
                    fee = st.number_input(
                        "Transaction Fee ($)", min_value=0.0, value=1.0, step=0.5
                    )
                with c1:
                    total = qty * current_price
                    st.metric(
                        label="Total Before Transaction Fee", value=f"${total:,.2f}"
                    )

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

                if btn_buy.button("🟢 BUY SHARES", use_container_width=True):
                    total_cost = total + fee  # Factoring in the fee

                    if st.session_state.balance >= total_cost:
                        st.session_state.balance -= total_cost
                        new_trade = {
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Ticker": ticker,
                            "Action": "BUY",
                            "Quantity": qty,
                            "Price": round(current_price, 2),
                            "Total": round(
                                total_cost, 2
                            ),  # Record the actual cash spent including fee
                        }
                        st.session_state.history = pd.concat(
                            [st.session_state.history, pd.DataFrame([new_trade])],
                            ignore_index=True,
                        )

                        update_balance(
                            st.session_state.username, st.session_state.balance
                        )
                        add_trade_to_db(st.session_state.username, new_trade)

                        st.success(
                            f"Bought {qty} shares of {ticker}! (Fee: ${fee:,.2f})"
                        )
                        st.rerun()
                    else:
                        st.error("Not enough cash!")

                if btn_sell.button("🔴 SELL SHARES", use_container_width=True):
                    if shares_owned >= qty:
                        total_revenue = total - fee  # Deducting the fee from earnings

                        st.session_state.balance += total_revenue
                        new_trade = {
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Ticker": ticker,
                            "Action": "SELL",
                            "Quantity": qty,
                            "Price": round(current_price, 2),
                            "Total": round(
                                total_revenue, 2
                            ),  # Record the actual cash received after fee
                        }
                        st.session_state.history = pd.concat(
                            [st.session_state.history, pd.DataFrame([new_trade])],
                            ignore_index=True,
                        )

                        update_balance(
                            st.session_state.username, st.session_state.balance
                        )
                        add_trade_to_db(st.session_state.username, new_trade)

                        st.success(f"Sold {qty} shares of {ticker}! (Fee: ${fee:,.2f})")
                        st.rerun()
                    else:
                        st.error(f"You only own {shares_owned} shares.")
            else:
                st.info("Enter a valid target ticker above to enable trading.")
