# ⚡ Paper Trader

A fast, minimalist virtual stock trading terminal built with Python and Streamlit.

Paper Trader allows multiple users to practice trading stocks in real-time using live market data, without risking real money. Every user gets a virtual $100,000 starting balance, and all trades, portfolios, and watchlists are safely saved to a cloud database.

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

## 🚀 How to Run Locally

If you want to run this app on your own computer, follow these steps:

### 1. Install Required Libraries

Open your terminal and install the necessary Python packages:

```bash
pip install streamlit yfinance pandas streamlit-autorefresh supabase
```
