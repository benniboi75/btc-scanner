import ccxt
import pandas as pd
import streamlit as st
import yfinance as yf

# Page configuration
st.set_page_config(
    page_title="BTC Tactical Scanner MTF", page_icon="🚦", layout="wide"
)

st.title("🚦 BTC Multi-Timeframe & Traffic Light Scanner")
st.markdown("---")


@st.cache_data(ttl=30)
def fetch_multi_tf_data():
  # Pulling multi-timeframe data to simulate MTF analysis
  df_1h = yf.download("BTC-USD", period="5d", interval="1h", progress=False)
  df_15m = yf.download("BTC-USD", period="1d", interval="15m", progress=False)

  for df in [df_1h, df_15m]:
    if isinstance(df.columns, pd.MultiIndex):
      df.columns = df.columns.get_level_values(0)
    # Calculate simple moving averages for trend signals
    df["EMA_Fast"] = df["Close"].ewm(span=9).mean()
    df["EMA_Slow"] = df["Close"].ewm(span=21).mean()

  return df_1h, df_15m


df_1h, df_15m = fetch_multi_tf_data()

# Determine Traffic Light & Arrow signals based on EMA crossovers
current_price = float(df_1h["Close"].iloc[-1])


def get_signal_state(df):
  fast = df["EMA_Fast"].iloc[-1]
  slow = df["EMA_Slow"].iloc[-1]
  if fast > slow:
    return "🟢 BULLISH", "⬆️"
  else:
    return "🔴 BEARISH", "⬇️"


tf_1h_status, tf_1h_arrow = get_signal_state(df_1h)
tf_15m_status, tf_15m_arrow = get_signal_state(df_15m)

# Top metrics row
col1, col2, col3 = st.columns(3)
with col1:
  st.metric("BTC Price", f"${current_price:,.2f}")
with col2:
  st.metric("1H Trend (Traffic Light)", tf_1h_status, tf_1h_arrow)
with col3:
  st.metric("15M Trend (Traffic Light)", tf_15m_status, tf_15m_arrow)

st.markdown("---")

# Layout charts and data tables
c1, c2 = st.columns([2, 1])

with c1:
  st.subheader("1H Price Action & Trend")
  st.line_chart(df_1h[["Close", "EMA_Fast", "EMA_Slow"]], height=350)

with c2:
  st.subheader("MTF Status Summary")
  status_df = pd.DataFrame({
      "Timeframe": ["1 Hour", "15 Minute"],
      "Signal": [tf_1h_status, tf_15m_status],
      "Direction": [tf_1h_arrow, tf_15m_arrow],
  })
  st.dataframe(status_df, use_container_width=True)

if st.button("🔄 Refresh Market Scans"):
  st.rerun()
