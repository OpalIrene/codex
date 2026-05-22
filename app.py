import streamlit as st
from pycoingecko import CoinGeckoAPI
import pandas as pd

cg = CoinGeckoAPI()

@st.cache_data(ttl=300)
def fetch_coin_markets(vs_currency="usd", ids=None):
    return cg.get_coins_markets(
        vs_currency=vs_currency,
        ids=ids,
        order="market_cap_desc",
        per_page=100,
        page=1,
        sparkline=False,
    )

@st.cache_data(ttl=3600)
def fetch_price_history(coin_id: str, vs_currency: str = "usd", days: int = 30) -> pd.DataFrame:
    chart = cg.get_coin_market_chart_by_id(
        id=coin_id,
        vs_currency=vs_currency,
        days=days,
        interval="daily",
    )
    df = pd.DataFrame(chart["prices"], columns=["timestamp", "price"])
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df.set_index("date")["price"]

@st.cache_data(ttl=3600)
def fetch_coin_ohlc(coin_id: str, vs_currency: str = "usd", days: int = 30) -> pd.DataFrame:
    ohlc_data = cg.get_coin_ohlc_by_id(
        id=coin_id,
        vs_currency=vs_currency,
        days=days,
    )
    df = pd.DataFrame(ohlc_data, columns=["timestamp", "open", "high", "low", "close"])
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df.set_index("date")[["open", "high", "low", "close"]]

st.set_page_config(
    page_title="CoinGecko Pulse",
    page_icon="💎",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp, .block-container {
        background-color: #0b1220;
        color: #e2e8f0;
    }
    [data-testid="stSidebar"] {
        background-color: #101827;
        color: #e2e8f0;
    }
    .css-1d391kg, .css-1v3fvcr, .css-1s7v0mw {
        background-color: #111b2e !important;
        color: #e2e8f0 !important;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown p {
        color: #e2e8f0 !important;
    }
    .stButton>button, button {
        background-color: #1f2937 !important;
        color: #e2e8f0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("CoinGecko Pulse — Crypto Market Intelligence")
st.markdown(
    "Explore top movers, a default watchlist with SUI, and rich market insights in a dark-mode dashboard."
)
st.caption("Created by ohhimac")

vs_currency = st.sidebar.selectbox("Quote currency", ["usd", "eur", "gbp"], index=0)
coin_search = st.sidebar.text_input("Search coins", value="bitcoin")
selected_days = st.sidebar.slider(
    "Price history days",
    min_value=7,
    max_value=90,
    value=30,
    step=7,
)

watchlist_ids = ["sui", "bitcoin", "ethereum", "solana", "chainlink"]
all_coins = fetch_coin_markets(vs_currency=vs_currency)
coins = all_coins
if coin_search:
    coins = [
        coin
        for coin in all_coins
        if coin_search.lower() in coin["name"].lower()
        or coin_search.lower() in coin["symbol"].lower()
    ]

watchlist_coins = [coin for coin in all_coins if coin["id"] in watchlist_ids]

gainers = sorted(
    all_coins,
    key=lambda coin: coin.get("price_change_percentage_24h") or 0,
    reverse=True,
)[:5]

if not coins:
    st.warning("No coins found. Try a different search term or currency.")
else:
    coins_df = pd.DataFrame(coins)
    coins_df = coins_df[
        [
            "market_cap_rank",
            "name",
            "symbol",
            "current_price",
            "price_change_percentage_24h",
            "market_cap",
            "total_volume",
        ]
    ]
    coins_df.columns = [
        "Rank",
        "Name",
        "Symbol",
        f"Price ({vs_currency.upper()})",
        "24h %",
        f"Market Cap ({vs_currency.upper()})",
        f"Volume ({vs_currency.upper()})",
    ]

    top_section, market_section = st.columns([1, 2])

    with top_section:
        st.subheader("Watchlist")
        if watchlist_coins:
            watch_cols = st.columns(len(watchlist_coins))
            for col, coin in zip(watch_cols, watchlist_coins):
                col.metric(
                    label=coin["name"],
                    value=f"{coin['current_price']:,}",
                    delta=f"{coin.get('price_change_percentage_24h', 0):.2f}%",
                )
        else:
            st.info("SUI watchlist coin is not currently in the top 100 list.")

        st.subheader("Top gainers (24h)")
        gainers_df = pd.DataFrame(gainers)
        gainers_df = gainers_df[
            [
                "market_cap_rank",
                "name",
                "symbol",
                "current_price",
                "price_change_percentage_24h",
            ]
        ]
        gainers_df.columns = [
            "Rank",
            "Name",
            "Symbol",
            f"Price ({vs_currency.upper()})",
            "24h %",
        ]
        st.dataframe(gainers_df, use_container_width=True)

    with market_section:
        st.subheader("Market overview")
        st.dataframe(coins_df.head(20), use_container_width=True)

        selected_coin = st.selectbox("Select coin for chart", coins_df["Name"].tolist())
        if selected_coin:
            coin_id = next(item["id"] for item in all_coins if item["name"] == selected_coin)
            history = fetch_price_history(
                coin_id,
                vs_currency=vs_currency,
                days=selected_days,
            )

            chart_col1, chart_col2 = st.columns(2)
            latest = coins_df.loc[coins_df["Name"] == selected_coin].iloc[0]
            chart_col1.metric(
                "Price",
                f"{latest[f'Price ({vs_currency.upper()})']:,}",
                f"{latest['24h %']:.2f}%",
            )
            chart_col2.metric(
                "Market Cap",
                f"{latest[f'Market Cap ({vs_currency.upper()})']:,}",
            )

            st.subheader(f"{selected_coin} price history ({selected_days} days)")
            st.line_chart(history)

            with st.expander("Candlestick chart structure"):
                st.write(
                    "This section is prepared for future OHLC candlestick support using CoinGecko data. "
                    "The data fetcher and UI container are ready to be extended with an interactive candlestick plot."
                )
                if st.button("Inspect candlestick data", key="load_ohlc"):
                    ohlc = fetch_coin_ohlc(
                        coin_id,
                        vs_currency=vs_currency,
                        days=selected_days,
                    )
                    if not ohlc.empty:
                        st.dataframe(ohlc.head())
                    else:
                        st.info("OHLC data is not available for this coin/timeframe yet.")

            st.markdown("---")
            st.write("### Raw market data")
            st.json(next(item for item in all_coins if item["name"] == selected_coin))
