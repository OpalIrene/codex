# codex
Repository for AI, automation, and development projects.

## Streamlit CoinGecko Dashboard
A lightweight Python dashboard built with Streamlit that uses the CoinGecko API to display crypto market data and historical price charts.

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

### Notes
- Data is sourced directly from the CoinGecko API.
- The app caches API results for better performance.
