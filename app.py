import streamlit as st
import yfinance as yf
import pandas as pd
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. APP CONFIG & AUTO-REFRESH ---
# This must be the very first Streamlit command
st.set_page_config(page_title="Paper Trader", layout="wide", page_icon="⚡")
st_autorefresh(interval=60000, limit=None, key="market_timer")

# --- 2. SECURITY BOUNCER ---
USER_ACCOUNTS = st.secrets["passwords"]
DATA_FOLDER = "data"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.logged_in:
    with st.container(border=True):
        st.title("🔒 Restricted Access")
        st.write("Please log in to your personal trading account.")

        with st.form("login_form", border=False):
            input_user = st.text_input("Username").lower()
            input_pass = st.text_input("Password", type="password")

            # This is a special button that listens for the 'Enter' key
            submit_button = st.form_submit_button(
                "Log In", type="primary", use_container_width=True
            )

            if submit_button:
                if (
                    input_user in USER_ACCOUNTS
                    and USER_ACCOUNTS[input_user] == input_pass
                ):
                    st.session_state.logged_in = True
                    st.session_state.username = input_user
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")

    st.stop()  # Stops the app here if not logged in


# --- 3. DATA STORAGE LOGIC ---
def load_data(username, data):
    # Files are now named after the user
    account_file = f"{data}/balance/{username}_balance.csv"
    trade_file = f"{data}/history/{username}_history.csv"
    watchlist_file = f"{data}/watchlist/{username}_watchlist.csv"

    if os.path.exists(account_file):
        balance = pd.read_csv(account_file)["balance"].iloc[0]
    else:
        balance = 100000.0

    if os.path.exists(trade_file):
        history = pd.read_csv(trade_file)
    else:
        history = pd.DataFrame(
            columns=["Timestamp", "Ticker", "Action", "Quantity", "Price", "Total"]
        )

    if os.path.exists(watchlist_file):
        watchlist = pd.read_csv(watchlist_file)["Ticker"].tolist()
    else:
        watchlist = []

    watchlist.sort()
    return balance, history, watchlist


def save_data(username, balance, history, watchlist):
    account_file = f"{username}_balance.csv"
    trade_file = f"{username}_history.csv"
    watchlist_file = f"{username}_watchlist.csv"

    pd.DataFrame({"balance": [balance]}).to_csv(account_file, index=False)
    history.to_csv(trade_file, index=False)
    pd.DataFrame({"Ticker": watchlist}).to_csv(watchlist_file, index=False)


# --- 4. LOAD USER DATA ---
balance, history, watchlist = load_data(st.session_state.username, DATA_FOLDER)

if "balance" not in st.session_state:
    st.session_state.balance = balance
if "history" not in st.session_state:
    st.session_state.history = history
if "watchlist" not in st.session_state:
    st.session_state.watchlist = watchlist

# --- 5. CALCULATE PORTFOLIO & AVERAGE PRICE ---
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

# --- 6. SIDEBAR: WALLET & SETTINGS ---
with st.sidebar:
    st.title("Paper Trader")
    st.write(f"👤 Logged in as: **{st.session_state.username.upper()}**")

    # WRAPPED IN A BOX
    with st.container(border=True):
        st.header("Wallet")
        st.metric("Available Cash", f"${st.session_state.balance:,.2f}")

    # WRAPPED IN A BOX
    with st.container(border=True):
        st.subheader("Your Stocks")
        if not portfolio.empty:
            st.dataframe(portfolio.set_index("Ticker"), use_container_width=True)
        else:
            st.write("*No stocks owned yet.*")

    # WRAPPED IN A BOX
    with st.container(border=True):
        st.subheader("⚙️ Account Settings")
        new_capital = st.number_input(
            "Starting Capital ($)", min_value=100.0, value=100000.0, step=1000.0
        )

        if st.button("⚠️ Restart Account", use_container_width=True):
            st.session_state.balance = new_capital
            st.session_state.history = pd.DataFrame(
                columns=["Timestamp", "Ticker", "Action", "Quantity", "Price", "Total"]
            )
            save_data(
                st.session_state.username,
                st.session_state.balance,
                st.session_state.history,
                st.session_state.watchlist,
            )
            st.rerun()

    # LOG OUT BUTTON
    if st.button("🚪 Log Out", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        # Clear the memory so the next person doesn't see your data briefly
        del st.session_state.balance
        del st.session_state.history
        del st.session_state.watchlist
        st.rerun()

# --- 7. MAIN INTERFACE ---
tab_terminal, tab_journal = st.tabs(["⚡ Market Terminal", "📜 Trade Journal"])

with tab_terminal:
    col_watch, col_trade = st.columns([1, 2], gap="large")

    # --- LEFT COLUMN: WATCHLIST ---
    with col_watch:

        # WIDGET 1: THE WATCHLIST DISPLAY
        with st.container(border=True):
            st.subheader("👀 Live Watchlist")

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

        # WIDGET 2: MANAGE WATCHLIST CONTROLS
        with st.container(border=True):
            st.subheader("⚙️ Manage List")

            # Add Stock Section (Aligned nicely)
            add_col1, add_col2 = st.columns([2, 1], vertical_alignment="bottom")
            with add_col1:
                new_ticker = st.text_input("Ticker to Add", key="add_t").upper()
            with add_col2:
                if st.button("➕ Add", use_container_width=True):
                    if new_ticker and new_ticker not in st.session_state.watchlist:
                        st.session_state.watchlist.append(new_ticker)
                        st.session_state.watchlist.sort()  # Keeps it A-Z
                        save_data(
                            st.session_state.username,
                            st.session_state.balance,
                            st.session_state.history,
                            st.session_state.watchlist,
                        )
                        st.rerun()

            # Remove Stock Section (Aligned nicely)
            if st.session_state.watchlist:
                rem_col1, rem_col2 = st.columns([2, 1], vertical_alignment="bottom")
                with rem_col1:
                    ticker_to_remove = st.selectbox(
                        "Ticker to Remove", st.session_state.watchlist
                    )
                with rem_col2:
                    if st.button("❌ Drop", use_container_width=True):
                        st.session_state.watchlist.remove(ticker_to_remove)
                        save_data(
                            st.session_state.username,
                            st.session_state.balance,
                            st.session_state.history,
                            st.session_state.watchlist,
                        )
                        st.rerun()

                # Clear All Button
                st.divider()  # Draws a neat line before the danger button
                if st.button(
                    "🗑️ Clear Entire Watchlist", type="primary", use_container_width=True
                ):
                    st.session_state.watchlist = []
                    save_data(
                        st.session_state.username,
                        st.session_state.balance,
                        st.session_state.history,
                        st.session_state.watchlist,
                    )
                    st.rerun()

    # --- RIGHT COLUMN: TRADE EXECUTION ---
    with col_trade:

        # LIVE QUOTE WRAPPED IN A BOX
        with st.container(border=True):
            st.subheader("Target Quote")
            ticker = st.text_input(
                "Enter Target Ticker (e.g., TSLA, AAPL)", "NVDA"
            ).upper()

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

        # EXECUTION WRAPPED IN A BOX
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
                        save_data(
                            st.session_state.username,
                            st.session_state.balance,
                            st.session_state.history,
                            st.session_state.watchlist,
                        )
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
                        save_data(
                            st.session_state.username,
                            st.session_state.balance,
                            st.session_state.history,
                            st.session_state.watchlist,
                        )
                        st.success(f"Sold {qty} shares of {ticker}!")
                        st.rerun()
                    else:
                        st.error(f"You only own {shares_owned} shares.")
            else:
                st.info("Enter a valid target ticker above to enable trading.")

# --- TAB 2: TRADE JOURNAL ---
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
