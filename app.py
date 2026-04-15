import pandas as pd
import streamlit as st
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

import auth
import dashboard
import journal
import terminal
import settings
import database

st.set_page_config(page_title="Paper Trading Lab", layout="wide", page_icon="💸")


def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("style.css")

st_autorefresh(interval=60000, limit=None, key="market_timer")

if not auth.check_password():
    st.stop()

if "balance" not in st.session_state:
    bal, hist, wl, fee = database.load_data(st.session_state.username)
    st.session_state.balance = bal
    st.session_state.history = hist
    st.session_state.watchlist = wl
    st.session_state.transaction_fee = fee


def handle_account_wipe(new_capital):
    st.session_state.balance = new_capital
    st.session_state.history = pd.DataFrame(
        columns=["Timestamp", "Ticker", "Action", "Quantity", "Price", "Total"]
    )
    database.wipe_account_data(st.session_state.username, new_capital)


portfolio_data = []
if not st.session_state.history.empty:
    df = st.session_state.history
    for t in df["Ticker"].unique():
        ticker_df = df[df["Ticker"] == t]
        buys = ticker_df[ticker_df["Action"] == "BUY"]
        sells = ticker_df[ticker_df["Action"] == "SELL"]

        total_bought = buys["Quantity"].sum() if not buys.empty else 0
        total_sold = sells["Quantity"].sum() if not sells.empty else 0
        current_qty = total_bought - total_sold

        if current_qty > 0:
            total_spent_on_buys = (buys["Quantity"] * buys["Price"]).sum()
            raw_avg = total_spent_on_buys / total_bought if total_bought > 0 else 0
            avg_buy_price = round(raw_avg, 2)

            portfolio_data.append(
                {
                    "Ticker": t,
                    "Quantity": current_qty,
                    "Avg Price": f"${avg_buy_price:.2f}",
                    "Raw Price": avg_buy_price,
                }
            )

portfolio = pd.DataFrame(portfolio_data)

# ---------------------------------------------------------
# NEW: THE SINGLE SOURCE OF TRUTH (MASTER FETCHER)
# ---------------------------------------------------------
# Combine everything you own AND everything you watch into one list
all_tickers_to_fetch = set(st.session_state.watchlist)
if not portfolio.empty:
    all_tickers_to_fetch.update(portfolio["Ticker"].tolist())

if all_tickers_to_fetch:
    tickers_list = list(all_tickers_to_fetch)
    batch_data = yf.download(tickers_list, period="1d", interval="1m", prepost=True)

    live_prices = {}
    for t in tickers_list:
        try:
            close_data = batch_data["Close"]
            if isinstance(close_data, pd.DataFrame):
                val = close_data[t].dropna().iloc[-1]
            else:
                val = close_data.dropna().iloc[-1]
            live_prices[t] = round(float(val), 2)
        except Exception:
            # Fallback for individual stock if batch fails
            try:
                raw_live = (
                    yf.Ticker(t)
                    .history(period="1d", interval="1m", prepost=True)["Close"]
                    .iloc[-1]
                )
                live_prices[t] = round(float(raw_live), 2)
            except:
                live_prices[t] = None

    # Write the fresh prices to the global "whiteboard"
    st.session_state.live_prices = live_prices
else:
    st.session_state.live_prices = {}
# ---------------------------------------------------------

with st.sidebar:
    st.sidebar.markdown(
        "<h2 style='text-align: left; font-size: 24px; font-family: \"Inter\", sans-serif;' class='main-logo'>Paper Trading Lab</h2>",
        unsafe_allow_html=True,
    )
    st.write(f"👤 Logged in as: **{st.session_state.username.upper()}**")

    with st.container(border=True):
        st.header("Wallet")
        st.metric("Available Cash", f"${st.session_state.balance:,.2f}")

    with st.container(border=True):
        st.subheader("Your Stocks")
        if not portfolio.empty:
            st.dataframe(
                portfolio.drop(columns=["Raw Price"]),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.write("*No stocks owned yet.*")

    if st.button("⚙️ Settings", use_container_width=True):
        settings.render_settings(handle_account_wipe)

    if st.button("🚪 Log Out", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        del st.session_state.balance
        del st.session_state.history
        del st.session_state.watchlist
        if "transaction_fee" in st.session_state:
            del st.session_state.transaction_fee
        st.rerun()

tab_dashboard, tab_terminal, tab_journal = st.tabs(
    [" 📊 Trader Dashboard ", " ⚡ Market Terminal ", " 📜 Trade Journal "]
)

with tab_terminal:
    terminal.render_terminal(portfolio)

with tab_dashboard:
    dashboard.render_dashboard(portfolio)

with tab_journal:
    journal.render_journal()
