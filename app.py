from datetime import datetime, timezone

import pandas as pd
import pytz
import streamlit as st
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

import auth
import dashboard
import database
import help_menu
import journal
import settings
import terminal


st.set_page_config(page_title="Paper Trading Lab", layout="wide", page_icon="💸")


def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("style.css")

st_autorefresh(interval=60000, limit=None, key="market_timer")

if not auth.check_password():
    st.stop()

if "balance" not in st.session_state:
    bal, hist, wl, fee, mho = database.load_data(st.session_state.username)
    st.session_state.balance = bal
    st.session_state.history = hist
    st.session_state.watchlist = wl
    st.session_state.transaction_fee = fee
    st.session_state.market_hours_only = mho


def handle_account_wipe(new_capital):
    st.session_state.balance = new_capital
    st.session_state.history = pd.DataFrame(
        columns=["Timestamp", "Ticker", "Action", "Quantity", "Price", "Total"]
    )
    database.wipe_account_data(st.session_state.username, new_capital)


portfolio_data = []
if not st.session_state.history.empty:

    df = st.session_state.history.sort_values(by="Timestamp")

    for t in df["Ticker"].unique():
        ticker_df = df[df["Ticker"] == t]

        current_qty = 0
        current_total_cost = 0.0

        for _, row in ticker_df.iterrows():
            action = row["Action"]
            qty = row["Quantity"]
            price = row["Price"]

            if action == "BUY":

                current_qty += qty
                current_total_cost += qty * price

            elif action == "SELL":
                if current_qty > 0:

                    avg_cost_before_sale = current_total_cost / current_qty

                    current_qty -= qty
                    current_total_cost -= avg_cost_before_sale * qty

                    if current_qty == 0:
                        current_total_cost = 0.0

        if current_qty > 0:
            avg_buy_price = round(current_total_cost / current_qty, 2)

            portfolio_data.append(
                {
                    "Ticker": t,
                    "Quantity": current_qty,
                    "Avg Price": f"${avg_buy_price:.2f}",
                    "Raw Price": avg_buy_price,
                }
            )

portfolio = pd.DataFrame(portfolio_data)

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

            try:
                raw_live = (
                    yf.Ticker(t)
                    .history(period="1d", interval="1m", prepost=True)["Close"]
                    .iloc[-1]
                )
                live_prices[t] = round(float(raw_live), 2)
            except:
                live_prices[t] = None

    st.session_state.live_prices = live_prices
else:
    st.session_state.live_prices = {}


with st.sidebar:
    st.sidebar.markdown(
        "<h2 style='text-align: left; font-size: 24px; font-family: \"Inter\", sans-serif;' class='main-logo'>Paper Trading Lab</h2>",
        unsafe_allow_html=True,
    )
    st.write(f"👤 Logged in as: **{st.session_state.username.upper()}**")

    user_tz_name = st.context.timezone or "UTC"
    user_tz = pytz.timezone(user_tz_name)
    local_now = datetime.now(timezone.utc).astimezone(user_tz)

    current_time = local_now.strftime("%H:%M")
    st.write(f"🕒 Local time: **{current_time}** ({user_tz_name})")

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

    if st.button("❓ Help Center", use_container_width=True):
        help_menu.render_help()

    if st.button("🚪 Log Out", use_container_width=True, type="primary"):
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
