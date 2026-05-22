import streamlit as st
from pycoingecko import CoinGeckoAPI
import pandas as pd

cg = CoinGeckoAPI()

@st.cache_data(ttl=300)
def fetch_coin_markets(vs_currency: str = "usd", ids: str | None = None) -> list[dict]:
    return cg.get_coins_markets(vs_currency=vs_currency, ids=ids, order="market_cap_desc", per_page=100, page=1, sparkline=False)

@st.cache_data(ttl=3600)
def fetch_price_history(coin_id: str, vs_currency: str = "usd", days: int = 30) -> pd.DataFrame:
    chart = cg.get_coin_market_chart_by_id(id=coin_id, vs_currency=vs_currency, days=days, interval="daily")
    df = pd.DataFrame(chart["prices"], columns=["timestamp", "price"])
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df.set_index("date")["price"]

st.set_page_config(page_title="CoinGecko Dashboard", page_icon="💰", layout="wide")

st.title("CoinGecko Crypto Dashboard")
st.markdown("Track live market data for top cryptocurrencies using the CoinGecko API.")

vs_currency = st.sidebar.selectbox("Quote currency", ["usd", "eur", "gbp"], index=0)
coin_search = st.sidebar.text_input("Search coins", value="bitcoin")
selected_days = st.sidebar.slider("Price history days", min_value=7, max_value=90, value=30, step=7)

coins = fetch_coin_markets(vs_currency=vs_currency)
if coin_search:
    coins = [coin for coin in coins if coin_search.lower() in coin["name"].lower() or coin_search.lower() in coin["symbol"].lower()]

if not coins:
    st.warning("No coins found. Try a different search term or currency.")
else:
    coins_df = pd.DataFrame(coins)
    coins_df = coins_df[["market_cap_rank", "name", "symbol", "current_price", "price_change_percentage_24h", "market_cap", "total_volume"]]
    coins_df.columns = ["Rank", "Name", "Symbol", f"Price ({vs_currency.upper()})", "24h %", f"Market Cap ({vs_currency.upper()})", f"Volume ({vs_currency.upper()})"]

    st.subheader("Market overview")
    st.dataframe(coins_df.head(20), use_container_width=True)

    selected_coin = st.selectbox("Select coin for chart", coins_df["Name"].tolist())
    if selected_coin:
        coin_id = next(item["id"] for item in coins if item["name"] == selected_coin)
        history = fetch_price_history(coin_id, vs_currency=vs_currency, days=selected_days)

        col1, col2 = st.columns(2)
        latest = coins_df.loc[coins_df["Name"] == selected_coin].iloc[0]
        col1.metric("Price", f"{latest[f'Price ({vs_currency.upper()})']:,}", f"{latest['24h %']:.2f}%")
        col2.metric("Market Cap", f"{latest[f'Market Cap ({vs_currency.upper()})']:,}")

        st.subheader(f"{selected_coin} price history ({selected_days} days)")
        st.line_chart(history)

        st.markdown("---")
        st.write("### Raw market data")
        st.json(next(item for item in coins if item["name"] == selected_coin))
