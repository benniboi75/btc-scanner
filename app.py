import ccxt
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="BTC Scanner", page_icon="📈", layout="centered"
)

st.title("⚡ BTC Market Scanner")
st.markdown("Live technical tracking and indicators dashboard.")


@st.cache_data(ttl=60)
def fetch_btc_data():
  try:
    exchange = ccxt.binance()
    ticker = exchange.fetch_ticker("BTC/USDT")
    return {
        "price": float(ticker["last"]),
        "high": float(ticker["high"]),
        "low": float(ticker["low"]),
        "volume": float(ticker["baseVolume"]),
    }
  except Exception:
    # Safe yfinance fallback with explicit scalar extraction
    df = yf.download("BTC-USD", period="1d", interval="1h", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
      df.columns = df.columns.get_level_values(0)
    latest_close = float(df["Close"].iloc[-1])
    high_val = float(df["High"].max())
    low_val = float(df["Low"].min())
    vol_val = float(df["Volume"].iloc[-1])
    return {
        "price": latest_close,
        "high": high_val,
        "low": low_val,
        "volume": vol_val,
    }


data = fetch_btc_data()

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

st.subheader("Price Action Chart")
history_data = yf.download("BTC-USD", period="5d", interval="1h", progress=False)
if not history_data.empty:
  if isinstance(history_data.columns, pd.MultiIndex):
    history_data.columns = history_data.columns.get_level_values(0)
  st.line_chart(history_data["Close"])

if st.button("🔄 Refresh Data"):
  st.rerun()
