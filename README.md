# 💸 Paper Trading Lab

![GitHub Release](https://img.shields.io/github/v/release/Bryanbu2014/paper-trading-lab)
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://paper-trading-lab.streamlit.app/)

A fast, minimalist virtual stock trading terminal built with Python and Streamlit.

Paper Trading Lab allows multiple users to practice trading stocks in real-time using live market data, without risking real money. Every user gets a virtual $100,000 starting balance, and all trades, portfolios, and watchlists are safely saved to a cloud database.

## ✨ Features

- **🔒 Secure User Login:** A built-in "Security Bouncer" ensures users can only access their own private accounts. Passwords are safely hidden using Streamlit Secrets.
- **☁️ Cloud Memory:** Powered by a PostgreSQL database (Supabase). Your trades, balance, and watchlists are saved permanently in the cloud, so nothing is lost when the app restarts.
- **📈 Live Market Data:** Fetches up-to-the-minute stock prices using the Yahoo Finance API (`yfinance`).
- **💼 Portfolio Tracking:** Automatically calculates how many shares you own and your average buy price.
- **👀 Quick Watchlist:** Add, drop, and view live prices for your favorite stocks. Easily add stocks by typing the ticker and hitting 'Enter'.
- **📜 Trade Journal:** A complete history of every buy and sell order you make.

## 🛠️ Tech Stack

- **Frontend & Backend UI:** [Streamlit](https://streamlit.io/)
- **Database:** [Supabase](https://supabase.com/) (PostgreSQL)
- **Market Data:** `yfinance`
- **Data Handling:** `pandas`

## 🔑 Requesting Access

The trading terminal is currently in a "Private Beta" to protect database resources. If you would like to test the app and start your own paper trading journey, please reach out to me!

**How to get an account:**

1. Send me a message via bubryanwb@gmail.com / [LinkedIn Wen Bin (Bryan) Bu](https://www.linkedin.com/in/bryanbuwb/).
2. Include your preferred **Username**.
3. I will set up your credentials and provide you with a password.

_Note: Once you have access, your portfolio and trade history will be saved exclusively to your account name._  
_Note: You are not allowed to change your password._
