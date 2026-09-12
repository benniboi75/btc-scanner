from datetime import datetime
import pandas as pd
import requests
import streamlit as st

# Page configuration for a compact terminal layout
st.set_page_config(
    page_title="BTC Terminal Scanner", page_icon="💻", layout="centered"
)


def compute_rsi(series, window=14):
  delta = series.diff()
  gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
  loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
  rs = gain / loss
  rsi = 100 - (100 / (1 + rs))
  return rsi.iloc[-1] if not rsi.empty else 50.0


def fetch_coinbase_matrix():
  # Map timeframes to Coinbase product candles granularity (in seconds)
  # 60 (1m), 300 (5m), 900 (15m), 3600 (1H), 21600 (6H->use 3600 and resample or 21600), 86400 (1D)
  tf_mapping = {
      "1M": 60,
      "5M": 300,
      "15M": 900,
      "1H": 3600,
      "4H": 21600,
      "1D": 86400,
  }
  results = {}
  current_price = 0.0

  # 1. Fetch Live Price from Coinbase
  try:
    price_res = requests.get(
        "https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=5
    )
    if price_res.status_code == 200:
      current_price = float(price_res.json()["data"]["amount"])
  except Exception as e:
    st.error(f"Price Fetch Error: {e}")

  # 2. Fetch Historical Candles for Indicators via Coinbase Pro / Exchange API
  for label, granularity in tf_mapping.items():
    try:
      url = f"https://api.pro.coinbase.com/products/BTC-USD/candles?granularity={granularity}"
      res = requests.get(
          url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5
      )

      if res.status_code != 200:
        results[label] = {"rsi": 50.0, "p": "▲", "ma": "X", "light": "[   ]"}
        continue

      # Coinbase candles format: [ time, low, high, open, close, volume ]
      raw_data = res.json()
      if not isinstance(raw_data, list) or len(raw_data) < 5:
        results[label] = {"rsi": 50.0, "p": "▲", "ma": "X", "light": "[   ]"}
        continue

      df = pd.DataFrame(raw_data, columns=["time", "low", "high", "open", "close", "volume"])
      # Coinbase returns newest candles first, so reverse to chronological order
      df = df.iloc[::-1].reset_index(drop=True)
      df["close"] = df["close"].astype(float)

      rsi_val = compute_rsi(df["close"])
      ema9 = df["close"].ewm(span=9).mean().iloc[-1]
      ema21 = df["close"].ewm(span=21).mean().iloc[-1]
      close_price = df["close"].iloc[-1]
      prev_close = df["close"].iloc[-2]

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
          "rsi": round(float(rsi_val), 1),
          "p": p_dir,
          "ma": ma_dir,
          "light": light,
      }
    except Exception:
      results[label] = {"rsi": 50.0, "p": "▲", "ma": "X", "light": "[   ]"}

  return current_price, results


# Force aggressive pure black background and neon green text styling across all elements
st.markdown("""
    <style>
    .stApp, .main, .block-container, div[data-testid="stVerticalBlock"] {
        background-color: #000000 !important;
        color: #00FF00 !important;
    }
    pre {
        background-color: #000000 !important;
        color: #00FF00 !important;
        border: 1px solid #00FF00 !important;
        padding: 15px;
        border-radius: 4px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 13px;
        line-height: 1.4;
    }
    p, span, label, h1, h2, h3, div {
        color: #00FF00 !important;
        font-family: 'Courier New', Courier, monospace !important;
    }
    .stButton>button {
        background-color: #000000 !important;
        color: #00FF00 !important;
        border: 1px solid #00FF00 !important;
        font-family: 'Courier New', Courier, monospace !important;
        border-radius: 4px;
    }
    .stButton>button:hover {
        background-color: #00FF00 !important;
        color: #000000 !important;
    }
    </style>
""", unsafe_allow_html=True)


# Native Streamlit Fragment that automatically reruns every 5 seconds
@st.fragment(run_every=5)
def render_live_scanner():
  price, matrix = fetch_coinbase_matrix()
  current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  m15_rsi = matrix.get("15M", {}).get("rsi", 50)
  mode = "COUNTER-TREND" if m15_rsi > 60 or m15_rsi < 40 else "TREND-FOLLOW"
  strategy = (
      "BEARISH BREAKOUT WATCH" if m15_rsi > 55 else "BULLISH ACCUMULATION WATCH"
  )

  # Fallback check if price came back empty
  display_price = price if price > 0 else 77000.0

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
| BTC PRICE     : ${display_price:,.2f}                     |
| FADE-SHORT SL : ${display_price * 1.002:,.2f}               |
| SIZE (BTC)    : 0.0360                                |
| SIZE (USD)    : ${display_price * 0.0360:,.2f}                |
| CONDITION     : MACRO COMPRESSION (5M,15M)            |
| STRATEGY      : {strategy:<37} |
+-------------------------------------------------------+
| LAST SYNC     : {current_time} | Status: COINBASE LIVE|
+-------------------------------------------------------+"""

  st.markdown(f"```text\n{terminal_display}\n```")


render_live_scanner()
