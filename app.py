from datetime import datetime
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from supabase import Client, create_client
import auth
import dashboard
import journal
import terminal
import setting

st.set_page_config(page_title="Paper Trading Lab", layout="wide", page_icon="💸")


def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("style.css")

st_autorefresh(interval=60000, limit=None, key="market_timer")

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

if not auth.check_password():
    st.stop()


def load_data(username):
    bal_res = (
        supabase.table("balances").select("balance").eq("username", username).execute()
    )
    balance = bal_res.data[0]["balance"] if bal_res.data else 100000.0

    hist_res = (
        supabase.table("trades")
        .select("Timestamp, Ticker, Action, Quantity, Price, Total")
        .eq("username", username)
        .execute()
    )
    if hist_res.data:
        history = pd.DataFrame(hist_res.data)
    else:
        history = pd.DataFrame(
            columns=["Timestamp", "Ticker", "Action", "Quantity", "Price", "Total"]
        )

    wl_res = (
        supabase.table("watchlists").select("ticker").eq("username", username).execute()
    )
    watchlist = [row["ticker"] for row in wl_res.data] if wl_res.data else []
    watchlist.sort()

    fee_res = (
        supabase.table("user_settings")
        .select("transaction_fee")
        .eq("username", username)
        .execute()
    )
    fee = fee_res.data[0]["transaction_fee"] if fee_res.data else 1.0

    return balance, history, watchlist, fee


def update_settings(username, fee):
    supabase.table("user_settings").upsert(
        {"username": username, "transaction_fee": fee}
    ).execute()


def update_balance(username, balance):
    supabase.table("balances").upsert(
        {"username": username, "balance": balance}
    ).execute()


def add_trade_to_db(username, trade_dict):
    db_trade = trade_dict.copy()
    db_trade["username"] = username
    supabase.table("trades").insert(db_trade).execute()


def update_watchlist(username, watchlist):
    supabase.table("watchlists").delete().eq("username", username).execute()
    if watchlist:
        records = [{"username": username, "ticker": t} for t in watchlist]
        supabase.table("watchlists").insert(records).execute()


def wipe_account_data(new_capital):

    st.session_state.balance = new_capital
    st.session_state.history = pd.DataFrame(
        columns=["Timestamp", "Ticker", "Action", "Quantity", "Price", "Total"]
    )

    update_balance(st.session_state.username, new_capital)
    supabase.table("trades").delete().eq(
        "username", st.session_state.username
    ).execute()
    supabase.table("net_worth_history").delete().eq(
        "username", st.session_state.username
    ).execute()


if "balance" not in st.session_state:
    bal, hist, wl, fee = load_data(st.session_state.username)
    st.session_state.balance = bal
    st.session_state.history = hist
    st.session_state.watchlist = wl
    st.session_state.transaction_fee = fee

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
            avg_buy_price = (
                total_spent_on_buys / total_bought if total_bought > 0 else 0
            )
            portfolio_data.append(
                {
                    "Ticker": t,
                    "Quantity": current_qty,
                    "Avg Price": f"${avg_buy_price:.2f}",
                }
            )

portfolio = pd.DataFrame(portfolio_data)

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
            st.dataframe(portfolio, use_container_width=True, hide_index=True)
        else:
            st.write("*No stocks owned yet.*")

    if st.button("⚙️ Settings", use_container_width=True):

        setting.render_settings(update_settings, wipe_account_data)

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
    terminal.render_terminal(
        portfolio, update_balance, add_trade_to_db, update_watchlist
    )

with tab_dashboard:
    dashboard.render_dashboard(portfolio, supabase)

with tab_journal:
    journal.render_journal()
