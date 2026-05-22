# CoinGecko Pulse — Crypto Market Intelligence

## Streamlit CoinGecko Dashboard
A lightweight Python dashboard built with Streamlit that uses the CoinGecko API to display crypto market data and historical price charts.

This app provides a dark-themed market intelligence dashboard with a default SUI watchlist, featured coins, top gainers, and a persistent market overview chart. Use the left-side Market Overview to browse the top coins and the right column to view featured coins, your watchlist, and top gainers.

### Run locally
1. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the app:
   ```bash
   streamlit run app.py
   ```

### Features
- Live market overview of top cryptocurrencies
- Search coins by name or symbol
- Price history chart for selected coin
- Metric cards for latest price and market cap

### How to view the Market Overview
- Open the app locally (`streamlit run app.py`).
- Use the sidebar search box labeled "Search coins" to filter results by coin name or symbol.
- The Market Overview table (left) updates to show matching coins; select a coin from the table to view its persistent price chart and metrics on the left.
- or go to: https://opalscryptodashboard.streamlit.app/

### Notes
- Data is sourced directly from the CoinGecko API.
- The app caches API results for better performance.
