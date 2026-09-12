import ccxt
import pandas as pd
import streamlit as st
import yfinance as yf

# Page configuration for a compact terminal layout
st.set_page_config(
    page_title="BTC Terminal Scanner", page_icon="💻", layout="centered"
)

# Custom CSS for pure black background, bright green text, and monospaced console styling
st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
        color: #00FF00;
        font-family: 'Courier New', Courier, monospace;
    }
    pre {
        background-color: #000000;
        color: #00FF00;
        border: 1px solid #00FF00;
        padding: 15px;
        border-radius: 4px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 13px;
        line-height: 1.4;
    }
    .stButton>button {
        background-color: #000000;
        color: #00FF00;
        border: 1px solid #00FF00;
        font-family: 'Courier New', Courier, monospace;
        border-radius: 4px;
    }
    .stButton>button:hover {
        background-color: #00FF00;
        color: #000000;
    }
    </style>
""", unsafe_allow_html=True)


# Technical Indicator Calculations
def compute_rsi(series, window=14):
  delta = series.diff()
  gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
  loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
  rs = gain / loss
  rsi = 100 - (100 / (1 + rs))
  return rsi.iloc[-1] if not rsi.empty else 50.0


@st.cache_data(ttl=15)
def fetch_live_matrix():
  tf_configs = {
      "1M": ("1m", "5d"),
      "5M": ("5m", "5d"),
      "15M": ("15m", "5d"),
      "1H": ("1h", "1mo"),
      "4H": ("1h", "1mo"),
      "1D": ("1d", "3mo"),
  }

  results = {}
  current_price = 0.0

  for label, (interval, period) in tf_configs.items():
    try:
      df = yf.download(
          "BTC-USD", period=period, interval=interval, progress=False
      )
      if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

      if label == "4H" and not df.empty:
        df = (
            df.resample("4H")
            .agg({
                "Open": "first",
                "High": "max",
                "Low": "min",
                "Close": "last",
                "Volume": "sum",
            })
            .dropna()
        )

      if df.empty or len(df) < 21:
        results[label] = {"rsi": 50.0, "p": "▲", "ma": "X", "light": "[   ]"}
        continue

      if label == "1M":
        current_price = float(df["Close"].iloc[-1])

      rsi_val = compute_rsi(df["Close"])
      ema9 = df["Close"].ewm(span=9).mean().iloc[-1]
      ema21 = df["Close"].ewm(span=21).mean().iloc[-1]
      close_price = df["Close"].iloc[-1]
      prev_close = df["Close"].iloc[-2]

      # Price Action & MA direction with traffic light symbols
      p_dir = "▲" if close_price >= prev_close else "▼"

      if ema9 > ema21:
        ma_dir = "▲"
        light = "[ 🟢 ]"
      elif ema9 < ema21:
        ma_dir = "▼"
        light = "[ 🔴 ]"
      else:
        ma_dir = "X"
        light = "[ 🟡 ]"

      results[label] = {
          "rsi": round(rsi_val, 1),
          "p": p_dir,
          "ma": ma_dir,
          "light": light,
      }
    except Exception:
      results[label] = {"rsi": 50.0, "p": "▲", "ma": "X", "light": "[   ]"}

  if current_price == 0.0:
    fallback = yf.download("BTC-USD", period="1d", interval="1h", progress=False)
    if isinstance(fallback.columns, pd.MultiIndex):
      fallback.columns = fallback.columns.get_level_values(0)
    current_price = float(fallback["Close"].iloc[-1])

  return current_price, results


price, matrix = fetch_live_matrix()

# Dynamic Mode & Strategy calculations
m15_rsi = matrix.get("15M", {}).get("rsi", 50)
mode = "COUNTER-TREND" if m15_rsi > 60 or m15_rsi < 40 else "TREND-FOLLOW"
strategy = (
    "BEARISH BREAKOUT WATCH" if m15_rsi > 55 else "BULLISH ACCUMULATION WATCH"
)

# Build exact terminal layout block matching your script
terminal_display = f"""+-------------------------------------------------------+
|  MULTI-TF SCANNER (Auto-Mode & Scrollable)            |
+-------------------------------------------------------+
| 1M     : RSI {matrix['1M']['rsi']:<4} | P: {matrix['1M']['p']}  | MA: {matrix['1M']['ma']}  {matrix['1M']['light']}        |
| 5M     : RSI {matrix['5M']['rsi']:<4} | P: {matrix['5M']['p']}  | MA: {matrix['5M']['ma']}  {matrix['5M']['light']}        |
| 15M(*) : RSI {matrix['15M']['rsi']:<4} | P: {matrix['15M']['p']}  | MA: {matrix['15M']['ma']}  {matrix['15M']['light']}        |
| 1H     : RSI {matrix['1H']['rsi']:<4} | P: {matrix['1H']['p']}  | MA: {matrix['1H']['ma']}  {matrix['1H']['light']}        |
| 4H     : RSI {matrix['4H']['rsi']:<4} | P: {matrix['4H']['p']}  | MA: {matrix['4H']['ma']}  {matrix['4H']['light']}        |
| 1D     : RSI {matrix['1D']['rsi']:<4} | P: {matrix['1D']['p']}  | MA: {matrix['1D']['ma']}  {matrix['1D']['light']}        |
+-------------------------------------------------------+
| MODE          : {mode:<37} |
| ACTIVE TF     : 15M                                   |
| BTC PRICE     : ${price:,.2f}                     |
| FADE-SHORT SL : ${price * 1.002:,.2f}               |
| SIZE (BTC)    : 0.0360                                |
| SIZE (USD)    : ${price * 0.0360:,.2f}                |
| CONDITION     : MACRO COMPRESSION (5M,15M)            |
| STRATEGY      : {strategy:<37} |
+-------------------------------------------------------+
| Controls: Web Live-Sync | Status: CONNECTED (5G)      |
+-------------------------------------------------------+"""

st.markdown(f"```text\n{terminal_display}\n```")

if st.button("🔄 REFRESH LIVE FEED"):
  st.rerun()
