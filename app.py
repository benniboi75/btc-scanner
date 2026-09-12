from datetime import datetime
import pandas as pd
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# Page configuration for a compact terminal layout
st.set_page_config(
    page_title="BTC Terminal Scanner", page_icon="💻", layout="centered"
)

# Automatically refresh the app every 5 seconds (5000 milliseconds)
st_autorefresh(interval=5000, limit=None, key="btc_auto_scanner")

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


def compute_rsi(series, window=14):
  delta = series.diff()
  gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
  loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
  rs = gain / loss
  rsi = 100 - (100 / (1 + rs))
  return rsi.iloc[-1] if not rsi.empty else 50.0


def fetch_binance_matrix():
  tf_mapping = {"1M": "1m", "5M": "5m", "15M": "15m", "1H": "1h", "4H": "4h", "1D": "1d"}
  results = {}
  current_price = 77000.0

  # Fetch live price directly from Binance public ticker
  try:
    ticker_res = requests.get(
        "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=3
    )
    if ticker_res.status_code == 200:
      current_price = float(ticker_res.json()["price"])
  except Exception:
    pass

  for label, interval in tf_mapping.items():
    try:
      url = f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval={interval}&limit=50"
      res = requests.get(url, timeout=3)
      if res.status_code != 200:
        results[label] = {"rsi": 50.0, "p": "▲", "ma": "X", "light": "[   ]"}
        continue

      raw_data = res.json()
      df = pd.DataFrame(raw_data, columns=[
          "open_time", "open", "high", "low", "close", "volume",
          "close_time", "quote_asset_volume", "number_of_trades",
          "taker_buy_base", "taker_buy_quote", "ignore"
      ])
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


price, matrix = fetch_binance_matrix()
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

m15_rsi = matrix.get("15M", {}).get("rsi", 50)
mode = "COUNTER-TREND" if m15_rsi > 60 or m15_rsi < 40 else "TREND-FOLLOW"
strategy = (
    "BEARISH BREAKOUT WATCH" if m15_rsi > 55 else "BULLISH ACCUMULATION WATCH"
)

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
| LAST SYNC     : {current_time} | Status: LIVE API     |
+-------------------------------------------------------+"""

st.markdown(f"```text\n{terminal_display}\n```")
