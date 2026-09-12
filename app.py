import ccxt
import pandas as pd
import streamlit as st
import yfinance as yf

# Page configuration for mobile-responsive view
st.set_page_config(
    page_title="BTC Scanner", page_icon="📈", layout="centered"
)

st.title("⚡ BTC Market Scanner")
st.markdown("Live technical tracking and indicators dashboard.")


# Fetch live data function
@st.cache_data(ttl=60)
def fetch_btc_data():
  try:
    # Example using CCXT for Binance/Exness data or yfinance fallback
    exchange = ccxt.binance()
    ticker = exchange.fetch_ticker("BTC/USDT")
    current_price = ticker["last"]
    high_24h = ticker["high"]
    low_24h = ticker["low"]
    volume = ticker["baseVolume"]

    return {
        "price": current_price,
        "high": high_24h,
        "low": low_24h,
        "volume": volume,
    }
  except Exception as e:
    # Fallback to yfinance if exchange API hits rate limits
    data = yf.download("BTC-USD", period="1d", interval="1h", progress=False)
    latest = data.iloc[-1]
    return {
        "price": float(latest["Close"]),
        "high": float(data["High"].max()),
        "low": float(data["Low"].min()),
        "volume": float(latest["Volume"]),
    }


# Load data
data = fetch_btc_data()

# Display metrics in a clean mobile-friendly layout
col1, col2 = st.columns(2)
with col1:
  st.metric(
      label="BTC Price",
      value=f"${data['price']:,.2f}",
      delta=f"High: ${data['high']:,.2f}",
  )
with col2:
  st.metric(
      label="24h Volume", value=f"{data['volume']:,.2f} BTC", delta="Active"
  )

st.divider()

# Historical Chart section
st.subheader("Price Action Chart")
history_data = yf.download("BTC-USD", period="5d", interval="1h", progress=False)
if not history_data.empty:
  # Flatten columns if multi-index is returned by yfinance
  if isinstance(history_data.columns, pd.MultiIndex):
    history_data.columns = history_data.columns.get_level_values(0)
  st.line_chart(history_data["Close"])

# Manual refresh button for mobile users
if st.button("🔄 Refresh Data"):
  st.rerent = True  # Trigger rerun
