from datetime import datetime

import pandas as pd
import streamlit as st
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
from supabase import Client, create_client

import auth

# --- APP CONFIG & AUTO-REFRESH ---
st.set_page_config(page_title="Paper Trading Lab", layout="wide", page_icon="💸")


# Read and inject the external CSS file
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Run the function
load_css("style.css")

st_autorefresh(interval=60000, limit=None, key="market_timer")

# --- SUPABASE SETUP ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- SECURITY BOUNCER ---
if not auth.check_password():
    st.stop()


# --- CLOUD DATABASE LOGIC ---
def load_data(username):
    # Fetch Balance
    bal_res = (
        supabase.table("balances").select("balance").eq("username", username).execute()
    )
    balance = bal_res.data[0]["balance"] if bal_res.data else 100000.0

    # Fetch History
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

    # Fetch Watchlist
    wl_res = (
        supabase.table("watchlists").select("ticker").eq("username", username).execute()
    )
    watchlist = [row["ticker"] for row in wl_res.data] if wl_res.data else []
    watchlist.sort()

    return balance, history, watchlist


def update_balance(username, balance):
    # Upsert updates the row if it exists, or creates it if it doesn't
    supabase.table("balances").upsert(
        {"username": username, "balance": balance}
    ).execute()


def add_trade_to_db(username, trade_dict):
    db_trade = trade_dict.copy()
    db_trade["username"] = username
    supabase.table("trades").insert(db_trade).execute()


def update_watchlist(username, watchlist):
    # Delete old list and insert the new one
    supabase.table("watchlists").delete().eq("username", username).execute()
    if watchlist:
        records = [{"username": username, "ticker": t} for t in watchlist]
        supabase.table("watchlists").insert(records).execute()


# --- LOAD USER DATA ---
# We only load from the database once when the app starts or user logs in
if "balance" not in st.session_state:
    bal, hist, wl = load_data(st.session_state.username)
    st.session_state.balance = bal
    st.session_state.history = hist
    st.session_state.watchlist = wl

# --- CALCULATE PORTFOLIO & AVERAGE PRICE ---
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

# --- SIDEBAR ---
with st.sidebar:
    st.sidebar.markdown(
        "<h2 style='text-align: left; font-size: 24px;' class='main-logo'>Paper Trading Lab</h2>",
        unsafe_allow_html=True,
    )
    st.write(f"👤 Logged in as: **{st.session_state.username.upper()}**")

    with st.container(border=True):
        st.header("Wallet")
        st.metric("Available Cash", f"${st.session_state.balance:,.2f}")

    with st.container(border=True):
        st.subheader("Your Stocks")
        if not portfolio.empty:
            st.dataframe(portfolio.set_index("Ticker"), use_container_width=True)
        else:
            st.write("*No stocks owned yet.*")

    with st.container(border=True):
        st.subheader("Account Settings")
        new_capital = st.number_input(
            "Starting Capital ($)", min_value=100.0, value=100000.0, step=1000.0
        )

        if st.button("⚠️ Restart Account", type="primary", use_container_width=True):
            st.session_state.balance = new_capital
            st.session_state.history = pd.DataFrame(
                columns=["Timestamp", "Ticker", "Action", "Quantity", "Price", "Total"]
            )

            # --- CLOUD WIPE ---
            update_balance(st.session_state.username, new_capital)
            supabase.table("trades").delete().eq(
                "username", st.session_state.username
            ).execute()

            st.rerun()

    if st.button("🚪 Log Out", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        del st.session_state.balance
        del st.session_state.history
        del st.session_state.watchlist
        st.rerun()

# --- MAIN INTERFACE ---
tab_terminal, tab_journal = st.tabs(["⚡ Market Terminal", "📜 Trade Journal"])

with tab_terminal:
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
                    # Changed st.button to st.form_submit_button
                    submit_add = st.form_submit_button(
                        "➕ Add", use_container_width=True
                    )

                # The logic runs if the button is clicked OR Enter is pressed
                if submit_add:
                    if new_ticker and new_ticker not in st.session_state.watchlist:
                        st.session_state.watchlist.append(new_ticker)
                        st.session_state.watchlist.sort()
                        # --- CLOUD SAVE ---
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
                        # --- CLOUD SAVE ---
                        update_watchlist(
                            st.session_state.username, st.session_state.watchlist
                        )
                        st.rerun()

                st.divider()
                if st.button(
                    "🗑️ Clear Entire Watchlist",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state.watchlist = []
                    # --- CLOUD SAVE ---
                    update_watchlist(
                        st.session_state.username, st.session_state.watchlist
                    )
                    st.rerun()

    with col_trade:
        with st.container(border=True):
            st.subheader("Target Quote")
            ticker = st.text_input("Enter Target Ticker (e.g., TSLA, AAPL)", "").upper()
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
                c1, c2 = st.columns([1, 1])
                with c1:
                    qty = st.number_input("Quantity to Trade", min_value=1, step=1)
                with c2:
                    total = qty * current_price
                    st.write("")
                    st.write(f"Total Value: **${total:,.2f}**")

                shares_owned = 0
                if not portfolio.empty and ticker in portfolio["Ticker"].values:
                    shares_owned = portfolio.loc[
                        portfolio["Ticker"] == ticker, "Quantity"
                    ].iloc[0]

                st.write(f"You currently own: **{shares_owned} shares**")

                btn_buy, btn_sell = st.columns(2)

                if btn_buy.button("🟢 BUY SHARES", use_container_width=True):
                    if st.session_state.balance >= total:
                        st.session_state.balance -= total
                        new_trade = {
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Ticker": ticker,
                            "Action": "BUY",
                            "Quantity": qty,
                            "Price": round(current_price, 2),
                            "Total": round(total, 2),
                        }
                        st.session_state.history = pd.concat(
                            [st.session_state.history, pd.DataFrame([new_trade])],
                            ignore_index=True,
                        )

                        # --- CLOUD SAVE ---
                        update_balance(
                            st.session_state.username, st.session_state.balance
                        )
                        add_trade_to_db(st.session_state.username, new_trade)

                        st.success(f"Bought {qty} shares of {ticker}!")
                        st.rerun()
                    else:
                        st.error("Not enough cash!")

                if btn_sell.button("🔴 SELL SHARES", use_container_width=True):
                    if shares_owned >= qty:
                        st.session_state.balance += total
                        new_trade = {
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Ticker": ticker,
                            "Action": "SELL",
                            "Quantity": qty,
                            "Price": round(current_price, 2),
                            "Total": round(total, 2),
                        }
                        st.session_state.history = pd.concat(
                            [st.session_state.history, pd.DataFrame([new_trade])],
                            ignore_index=True,
                        )

                        # --- CLOUD SAVE ---
                        update_balance(
                            st.session_state.username, st.session_state.balance
                        )
                        add_trade_to_db(st.session_state.username, new_trade)

                        st.success(f"Sold {qty} shares of {ticker}!")
                        st.rerun()
                    else:
                        st.error(f"You only own {shares_owned} shares.")
            else:
                st.info("Enter a valid target ticker above to enable trading.")

with tab_journal:
    with st.container(border=True):
        st.subheader("Transaction Log")
        if not st.session_state.history.empty:
            st.dataframe(
                st.session_state.history.iloc[::-1],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No trades have been recorded yet.")
