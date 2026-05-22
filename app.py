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
    chart = cg.get_coin_market_chart_by_id(id=coin_id, vs_currency=vs_currency, days=days)
    prices = chart.get("prices", [])
    if not prices:
        return pd.DataFrame()
    df = pd.DataFrame(prices, columns=["timestamp", "price"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.set_index("timestamp")
    return df["price"].rename("price").to_frame()


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
    if v >= 1_000_000_000:
        return f"${v/1_000_000_000:.2f}B"
    if v >= 1_000_000:
        return f"${v/1_000_000:.2f}M"
    if v >= 1_000:
        return f"${v/1_000:.2f}k"
    return f"${v:,.2f}"


st.set_page_config(page_title="CoinGecko Pulse", page_icon="💎", layout="wide")

st.markdown(
    """
    <style>
    .stApp, .block-container { background-color: #0b1220; color: #e2e8f0; }
    [data-testid="stSidebar"] { background-color: #101827; color: #e2e8f0; }
    .stButton>button, button { background-color: #1f2937 !important; color: #e2e8f0 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("CoinGecko Pulse — Crypto Market Intelligence")
st.caption("Created by Opal Fraser")

# Quick usage instructions shown on the dashboard for first-time users
st.markdown(
    """
    **How to view the Market Overview:**

    Use the sidebar Search coins box to filter by coin name or symbol.

    The Market Overview table on the left updates to show matching coins.

    Selecting a coin displays its persistent price chart and metrics on the left.
    """,
    unsafe_allow_html=True,
)

# Sidebar
price_format = st.sidebar.selectbox(
    "Price format", ["Auto (2/4/6)", "2 decimals", "4 decimals", "6 decimals"], index=0
)
vs_currency = st.sidebar.selectbox("Quote currency", ["USD", "EUR", "GBP"], index=0).lower()
coin_search = st.sidebar.text_input("Search coins", value="Bitcoin")
selected_days = st.sidebar.slider("Price history days", 7, 90, 30, step=7)

watchlist_ids = ["sui", "bitcoin", "ethereum", "solana", "chainlink"]
all_coins = fetch_coin_markets(vs_currency=vs_currency)
coins = all_coins
if coin_search:
    coins = [
        coin
        for coin in all_coins
        if coin_search.lower() in coin["name"].lower() or coin_search.lower() in coin["symbol"].lower()
    ]

watchlist_coins = [coin for coin in all_coins if coin["id"] in watchlist_ids]

gainers = sorted(all_coins, key=lambda c: c.get("price_change_percentage_24h") or 0, reverse=True)[:5]

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

    left_col, right_col = st.columns([1.6, 1])

    # Left: Market overview + persistent chart
    with left_col:
        st.subheader("Market overview")
        display_df = coins_df.copy()
        price_col = f"Price ({vs_currency.upper()})"
        market_col = f"Market Cap ({vs_currency.upper()})"
        vol_col = f"Volume ({vs_currency.upper()})"
        if price_col in display_df.columns:
            display_df[price_col] = display_df[price_col].apply(lambda x: format_price(x, price_format, vs_currency))
        if "Symbol" in display_df.columns:
            display_df["Symbol"] = display_df["Symbol"].str.upper()
        if market_col in display_df.columns:
            display_df[market_col] = display_df[market_col].apply(format_large_number)
        if vol_col in display_df.columns:
            display_df[vol_col] = display_df[vol_col].apply(format_large_number)

        st.dataframe(display_df.head(20), width="stretch")
        selected = st.selectbox("Select coin for chart", display_df["Name"].tolist(), key="market_select")
        if selected:
            coin_id = next(item["id"] for item in all_coins if item["name"] == selected)
            history = fetch_price_history(coin_id, vs_currency=vs_currency, days=selected_days)
            latest = display_df.loc[display_df["Name"] == selected].iloc[0]
            st.metric("Price", latest[price_col], f"{float(latest['24h %']):.2f}%")
            st.metric("Market Cap", format_large_number(coins_df.loc[coins_df["Name"] == selected].iloc[0][market_col]))
            st.subheader(f"{selected} price history ({selected_days} days)")
            st.line_chart(history)

    # Right: Featured, Watchlist, Top Gainers
    with right_col:
        featured_ids = ["bitcoin", "ethereum", "sui", "solana", "ondo"]
        featured_coins = [c for c in all_coins if c["id"] in featured_ids]
        if featured_coins:
            st.subheader("Featured coins")
            feat_df = pd.DataFrame(featured_coins)[["market_cap_rank", "name", "symbol", "current_price", "price_change_percentage_24h", "market_cap"]]
            feat_df.columns = ["Rank", "Name", "Symbol", f"Price ({vs_currency.upper()})", "24h %", f"Market Cap ({vs_currency.upper()})"]
            feat_df["Symbol"] = feat_df["Symbol"].str.upper()
            price_col_feat = f"Price ({vs_currency.upper()})"
            feat_df[price_col_feat] = feat_df[price_col_feat].apply(lambda x: format_price(x, price_format, vs_currency))
            feat_df[f"Market Cap ({vs_currency.upper()})"] = feat_df[f"Market Cap ({vs_currency.upper()})"].apply(format_large_number)
            st.dataframe(feat_df, width="content")

        st.subheader("Watchlist")
        if watchlist_coins:
            watch_cols = st.columns([1] * len(watchlist_coins))
            for col, coin in zip(watch_cols, watchlist_coins):
                logo = coin.get("image", "")
                sym = coin.get("symbol", coin.get("id", "")).upper()
                price = format_price(coin.get("current_price", 0), price_format, vs_currency)
                delta = coin.get("price_change_percentage_24h", 0) or 0
                html = f"""
                <div style='background:#0f1724;padding:10px;border-radius:10px;text-align:center;color:#e2e8f0;'>
                  <img src='{logo}' width=28 height=28 style='border-radius:50%;'/>
                  <div style='font-weight:700;margin-top:6px;'>{sym}</div>
                  <div style='font-size:14px;margin-top:4px;font-weight:600;'>{price}</div>
                  <div style='color:{'lime' if delta>=0 else 'salmon'};font-weight:600;margin-top:4px;'>{delta:.2f}%</div>
                </div>
                """
                col.markdown(html, unsafe_allow_html=True)
        else:
            st.info("SUI watchlist coin is not currently in the top 100 list.")

        st.subheader("Top gainers (24h)")
        gainers_df = pd.DataFrame(gainers)[["market_cap_rank", "name", "symbol", "current_price", "price_change_percentage_24h"]]
        gainers_df.columns = ["Rank", "Name", "Symbol", f"Price ({vs_currency.upper()})", "24h %"]
        gainers_df["Symbol"] = gainers_df["Symbol"].str.upper()
        price_col_g = f"Price ({vs_currency.upper()})"
        gainers_df[price_col_g] = gainers_df[price_col_g].apply(lambda x: format_price(x, price_format, vs_currency))
        st.dataframe(gainers_df, width="stretch")
