import streamlit as st

@st.dialog("❓ Help Center")
def render_help():
    st.markdown("""
    Welcome to the **Paper Trading Lab**! This laboratory is designed to help you practice trading strategies with zero financial risk.
    
    ### ⚡ Market Terminal
    The Terminal is where all the action happens.
    1. **Live Watchlist**: Add tickers (e.g., `AAPL`, `TSLA`, `BTC-USD`) to track prices in real-time. Use the 'Clear' button to reset your list.
    2. **Execution Price**: We use **Trade Republic style pricing**. 
       - Your transaction fee ($1.00 by default) is spread across the shares you buy/sell. 
       - **Buy Price** = Market Price + (Fee / Quantity)
       - **Sell Price** = Market Price - (Fee / Quantity)
    3. **Trading Hours**: If enabled in Settings, trading is restricted to US Extended Hours (**4:00 AM – 8:00 PM ET**).
    
    ### 📊 Trader Dashboard
    Track your performance and wealth.
    - **Net Worth**: Your current cash + the market value of all stocks you own.
    - **Unrealized P/L**: Profit or loss on stocks you are currently holding.
    - **Realized P/L**: Profit or loss locked in from stocks you have already sold.
    - **Performance History**: A daily log of your account's value and gains.
    
    ### 📜 Trade Journal
    A complete chronological list of every trade you've ever made. You can use this to review your entry and exit points.
    
    ### ⚙️ Settings
    - **Transaction Fee**: Customize how much each trade costs you.
    - **Market Hours**: Toggle the trading restriction on or off.
    - **Restart Account**: Wipe all data and start fresh with a new balance.
    
    ---
    *Need more help? Contact the administrator to reset your credentials or request new features.*
    """)
