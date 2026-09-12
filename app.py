import ccxt
import pandas as pd
import streamlit as st
import yfinance as yf

# Page configuration for compact view
st.set_page_config(
    page_title="BTC Terminal Scanner", page_icon="💻", layout="wide"
)

# Custom CSS for terminal monospaced look and dark background
st.markdown("""
    <style>
    .stApp {
        background-color: #0b0f19;
        color: #e6edf3;
        font-family: 'Courier New', Courier, monospace;
    }
    div.stMetric {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 10px;
        border-radius: 4px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown(
    "### 💻 BTC CMD TACTICAL SCANNER [EXNESS/BINANCE]", unsafe_allow_html=True
)
st.markdown("---")


@st.cache_data(ttl=30)
def fetch_cmd_data():
  df_1h = yf.download("BTC-USD", period="3d", interval="1h", progress=False)
  df_15m = yf.download("BTC-USD", period="1d", interval="15m", progress=False)

  for df in [df_1h, df_15m]:
    if isinstance(df.columns, pd.MultiIndex):
      df.columns = df.columns.get_level_values(0)
    df["EMA9"] = df["Close"].ewm(span=9).mean()
    df["EMA21"] = df["Close"].ewm(span=21).mean()
    df["ATR"] = df["High"] - df["Low"]

  return df_1h, df_15m


df_1h, df_15m = fetch_cmd_data()

# Calculations
price = float(df_1h["Close"].iloc[-1])
high_24h = float(df_1h["High"].max())
low_24h = float(df_1h["Low"].min())
vol_24h = float(df_1h["Volume"].iloc[-1])


def get_status(df):
  if df["EMA9"].iloc[-1] > df["EMA21"].iloc[-1]:
    return "🟢 BULLISH", "⬆"
  return "🔴 BEARISH", "⬇"


trend_1h, arrow_1h = get_status(df_1h)
trend_15m, arrow_15m = get_status(df_15m)

# Terminal-style top status grid
col1, col2, col3, col4 = st.columns(4)
with col1:
  st.metric("PRICE", f"${price:,.2f}")
with col2:
  st.metric("1H TREND", f"{trend_1h} {arrow_1h}")
with col3:
  st.metric("15M TREND", f"{trend_15m} {arrow_15m}")
with col4:
  st.metric("24H RANGE", f"${low_24h:,.0f} - ${high_24h:,.0f}")

st.markdown("---")

# Compact Terminal Data Log Table instead of bulky line charts
st.markdown("#### 📊 MULTI-TIMEFRAME ENGINE LOGS")

log_data = {
    "Timeframe": ["1 Hour", "15 Minute"],
    "Close Price": [
        f"${df_1h['Close'].iloc[-1]:,.2f}",
        f"${df_15m['Close'].iloc[-1]:,.2f}",
    ],
    "EMA 9": [
        f"${df_1h['EMA9'].iloc[-1]:,.2f}",
        f"${df_15m['EMA9'].iloc[-1]:,.2f}",
    ],
    "EMA 21": [
        f"${df_1h['EMA21'].iloc[-1]:,.2f}",
        f"${df_15m['EMA21'].iloc[-1]:,.2f}",
    ],
    "Signal Status": [trend_1h, trend_15m],
}

log_df = pd.DataFrame(log_data)
st.dataframe(log_df, use_container_width=True, hide_index=True)

# Manual refresh for fast execution loops
if st.button("🔄 REFRESH TICK FEED"):
  st.rerun()
