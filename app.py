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


def format_price(value: float, mode: str = "Auto (2/4/6)", currency: str = "usd") -> str:
    try:
        v = float(value)
    except Exception:
        return str(value)
    if currency.lower() == "usd":
        return f"{v:,.2f}"
    if mode == "2 decimals":
        return f"{v:,.2f}"
    if mode == "4 decimals":
        return f"{v:,.4f}"
    if mode == "6 decimals":
        return f"{v:,.6f}"
    # Auto mode
    if v >= 1:
        return f"{v:,.2f}"
    elif v >= 0.01:
        return f"{v:,.4f}"
    else:
        return f"{v:,.6f}"


def format_large_number(value: float) -> str:
    try:
        v = float(value)
    except Exception:
        return str(value)
    return f"{v:,.0f}"

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
st.markdown("Explore top movers, a default watchlist with SUI, and rich market insights in a dark-mode dashboard.")

# Sidebar: formatting options
price_format = st.sidebar.selectbox(
    "Price format",
    ["Auto (2/4/6)", "2 decimals", "4 decimals", "6 decimals"],
    index=0,
)

st.caption("Created by Opal Fraser")

vs_currency = st.sidebar.selectbox("Quote currency", ["USD", "EUR", "GBP"], index=0).lower()
coin_search = st.sidebar.text_input("Search coins", value="Bitcoin")
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

    top_section, market_section = st.columns([1.2, 1])

    with top_section:
        st.subheader("Watchlist")
        if watchlist_coins:
            # Use compact symbols (e.g. BTC, ETH) and give slightly wider columns
            watch_cols = st.columns([1.3] * len(watchlist_coins))
            for col, coin in zip(watch_cols, watchlist_coins):
                logo_url = coin.get("image", "")
                symbol = coin.get("symbol", coin.get("id", "")).upper()
                price_str = format_price(coin.get("current_price", 0), price_format, vs_currency)
                delta = coin.get("price_change_percentage_24h", 0) or 0
                # Render a compact logo card with hover tooltip showing full coin name
                card_html = f"""
                <div title="{coin.get('name', '')}" style="background:#0f1724;padding:12px;border-radius:12px;text-align:center;color:#e2e8f0;min-height:140px;">
                  <div style="display:flex;align-items:center;justify-content:center;margin-bottom:8px;">
                    <img src=\"{logo_url}\" width=30 height=30 style=\"border-radius:50%;margin-right:8px;\" />
                    <div style=\"font-weight:700;font-size:14px;\">{symbol}</div>
                  </div>
                  <div style="font-size:16px;font-weight:700;margin-top:4px;">{price_str}</div>
                  <div style="font-size:13px;color:{'lime' if delta>=0 else 'salmon'};font-weight:600;margin-top:6px;">{delta:.2f}%</div>
                </div>
                """
                col.markdown(card_html, unsafe_allow_html=True)
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
        gainers_df["Symbol"] = gainers_df["Symbol"].str.upper()
        # Format price column for display
        price_col_g = f"Price ({vs_currency.upper()})"
        if price_col_g in gainers_df.columns:
            gainers_df[price_col_g] = gainers_df[price_col_g].apply(lambda x: format_price(x, price_format, vs_currency))
        st.dataframe(gainers_df, width='stretch')

    with market_section:
        # Featured coins (ensure these appear at top of market view)
        featured_ids = ["bitcoin", "ethereum", "sui", "solana", "ondo"]
        featured_coins = [c for c in all_coins if c["id"] in featured_ids]
        if featured_coins:
            feat_df = pd.DataFrame(featured_coins)[[
                "market_cap_rank",
                "name",
                "symbol",
                "current_price",
                "price_change_percentage_24h",
                "market_cap",
            ]]
            feat_df.columns = [
                "Rank",
                "Name",
                "Symbol",
                f"Price ({vs_currency.upper()})",
                "24h %",
                f"Market Cap ({vs_currency.upper()})",
            ]
            feat_df["Symbol"] = feat_df["Symbol"].str.upper()
            # Format prices
            price_col_feat = f"Price ({vs_currency.upper()})"
            if price_col_feat in feat_df.columns:
                feat_df[price_col_feat] = feat_df[price_col_feat].apply(lambda x: format_price(x, price_format, vs_currency))
            feat_df[f"Market Cap ({vs_currency.upper()})"] = feat_df[f"Market Cap ({vs_currency.upper()})"].apply(format_large_number)
            st.subheader("Featured coins")
            st.dataframe(feat_df, width='content')

        st.subheader("Market overview")
        # Format price/market cap/volume for display
        price_col = f"Price ({vs_currency.upper()})"
        market_col = f"Market Cap ({vs_currency.upper()})"
        vol_col = f"Volume ({vs_currency.upper()})"
        display_df = coins_df.copy()
        if price_col in display_df.columns:
            display_df[price_col] = display_df[price_col].apply(lambda x: format_price(x, price_format, vs_currency))
        if "Symbol" in display_df.columns:
            display_df["Symbol"] = display_df["Symbol"].str.upper()
        if market_col in display_df.columns:
            display_df[market_col] = display_df[market_col].apply(format_large_number)
        if vol_col in display_df.columns:
            display_df[vol_col] = display_df[vol_col].apply(format_large_number)

        market_left, market_right = st.columns([1.4, 1])

        with market_left:
            st.dataframe(display_df.head(20), width='stretch')
            selected_coin = st.selectbox("Select coin for chart", coins_df["Name"].tolist(), key="market_select")

        with market_right:
            if selected_coin:
                coin_id = next(item["id"] for item in all_coins if item["name"] == selected_coin)
                history = fetch_price_history(
                    coin_id,
                    vs_currency=vs_currency,
                    days=selected_days,
                )

                latest = display_df.loc[display_df["Name"] == selected_coin].iloc[0]
                st.metric(
                    "Price",
                    latest[f"Price ({vs_currency.upper()})"],
                    f"{float(latest['24h %']):.2f}%",
                )
                st.metric(
                    "Market Cap",
                    format_large_number(coins_df.loc[coins_df["Name"] == selected_coin].iloc[0][f"Market Cap ({vs_currency.upper()})"]),
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
