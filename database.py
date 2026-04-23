from datetime import datetime, timezone
import pandas as pd
import pytz
import streamlit as st
from supabase import Client, create_client

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)


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


def update_watchlist(username, watchlist):
    supabase.table("watchlists").delete().eq("username", username).execute()
    if watchlist:
        records = [{"username": username, "ticker": t} for t in watchlist]
        supabase.table("watchlists").insert(records).execute()


def add_trade(username, trade_dict):
    db_trade = trade_dict.copy()
    db_trade["username"] = username
    supabase.table("trades").insert(db_trade).execute()


def wipe_account_data(username, new_capital):
    update_balance(username, new_capital)
    supabase.table("trades").delete().eq("username", username).execute()
    supabase.table("net_worth_history").delete().eq("username", username).execute()


def save_daily_net_worth(username, current_total_value):
    user_tz_name = st.context.timezone or "Europe/Berlin"
    user_tz = pytz.timezone(user_tz_name)

    now_utc = datetime.now(timezone.utc)
    local_now = now_utc.astimezone(user_tz)

    today = local_now.date().isoformat()

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


def get_net_worth_history(username):
    history_res = (
        supabase.table("net_worth_history")
        .select("timestamp, net_worth")
        .eq("username", username)
        .execute()
    )
    if history_res.data:
        return pd.DataFrame(history_res.data)
    return None
