from datetime import datetime
import pandas as pd
import requests
import streamlit as st

# Page configuration for a compact terminal layout
st.set_page_config(
    page_title="BTC Terminal Scanner", page_icon="💻", layout="centered"
)

# Force aggressive pure black background, neon green text, and disable all transitions/flashing
st.markdown("""
    <style>
    /* Disable all default browser/Streamlit transition fades and animations to stop flashing */
    *, *:before, *:after {
        transition: none !important;
        animation: none !important;
    }
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
    section[data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid #00FF00;
    }
    section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] div {
        color: #00FF00 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR CONTROLS ---
st.sidebar.markdown("### 🎛️ TERMINAL CONTROLS")
selected_tf = st.sidebar.selectbox(
    "Active Timeframe", ["1M", "5M", "15M", "1H", "4H", "1D"], index=2
)
selected_mode = st.sidebar.selectbox(
    "Trading Mode", ["AUTO", "COUNTER-TREND", "TREND-FOLLOW"], index=0
)
st.sidebar.markdown("---")
st.sidebar.markdown("Status: **Connected to Kraken Live API**")


def compute_rsi(series, window=14):
  delta = series.diff()
  gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
  loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
  rs = gain / loss
  rsi = 100 - (100 / (1 + rs))
  return rsi.iloc[-1] if not rsi.empty else 50.0


def fetch_kraken_matrix():
  tf_mapping = {
      "1M": 1,
      "5M": 5,
      "15M": 15,
      "1H": 60,
      "4H": 240,
      "1D": 1440,
  }
  results = {}
  current_price = 0.0

  try:
    ticker_res = requests.get(
        "https://api.kraken.com/0/public/Ticker?pair=XBTUSD", timeout=5
    )
    if ticker_res.status_code == 200:
      data = ticker_res.json()
      pair_key = (
          "XXBTZUSD" if "XXBTZUSD" in data.get("result", {}) else "BTCUSD"
      )
      if pair_key in data["result"]:
        current_price = float(data["result"][pair_key]["c"][0])
  except Exception as e:
    st.error(f"Kraken Price Error: {e}")

  for label, interval in tf_mapping.items():
    try:
      url = f"https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval={interval}"
      res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)

      if res.status_code != 200:
        results[label] = {"rsi": 50.0, "p": "▲", "ma": "X", "light": "[   ]"}
        continue

      payload = res.json()
      if "result" not in payload:
        results[label] = {"rsi": 50.0, "p": "▲", "ma": "X", "light": "[   ]"}
        continue

      result_keys = [k for k in payload["result"].keys() if k != "last"]
      if not result_keys:
        results[label] = {"rsi": 50.0, "p": "▲", "ma": "X", "light": "[   ]"}
        continue

      raw_candles = payload["result"][result_keys[0]]
      df = pd.DataFrame(
          raw_candles,
          columns=[
              "time",
              "open",
              "high",
              "low",
              "close",
              "vwap",
              "volume",
              "count",
          ],
      )
      df["close"] = df["close"].astype(float)

      if len(df) < 15:
        results[label] = {"rsi": 50.0, "p": "▲", "ma": "X", "light": "[   ]"}
        continue

      rsi_val = compute_rsi(df["close"])
      ema9 = df["close"].ewm(span=9).mean().iloc[-1]
      ema21 = df["close"].ewm(span=21).mean().iloc[-1]
      close_price = df["close"].iloc[-1]
      prev_close = df["close"].iloc[-2]

      p_dir = "▲" if close_price >= prev_close else "▼"

      # Determine EMA direction
      if ema9 > ema21:
        ma_dir = "▲"
      elif ema9 < ema21:
        ma_dir = "▼"
      else:
        ma_dir = "X"

      # Traffic Lights reflecting RSI ONLY
      if rsi_val > 55:
        light = "[ 🟢 ]"
      elif rsi_val < 45:
        light = "[ 🔴 ]"
      else:
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


# Native Streamlit Fragment that automatically reruns every 5 seconds
@st.fragment(run_every=5)
def render_live_scanner(active_tf, mode_override):
  price, matrix = fetch_kraken_matrix()
  current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  tf_rsi = matrix.get(active_tf, {}).get("rsi", 50)

  if mode_override == "AUTO":
    mode = "COUNTER-TREND" if tf_rsi > 60 or tf_rsi < 40 else "TREND-FOLLOW"
  else:
    mode = mode_override

  strategy = (
      "BEARISH BREAKOUT WATCH" if tf_rsi > 55 else "BULLISH ACCUMULATION WATCH"
  )
  display_price = price if price > 0 else 77000.0

  rows = []
  for tf in ["1M", "5M", "15M", "1H", "4H", "1D"]:
    label_str = f"{tf.ljust(4)}(*)" if tf == active_tf else f"{tf.ljust(7)}"
    m_data = matrix.get(
        tf, {"rsi": 50.0, "p": "▲", "ma": "X", "light": "[   ]"}
    )
    rows.append(
        f"| {label_str} : RSI {str(m_data['rsi']).ljust(4)} | P: {m_data['p']}"
        f"  | MA: {m_data['ma']}  {m_data['light'].ljust(6)} |"
    )

  rows_joined = "\n".join(rows)

  terminal_display = f"""+-------------------------------------------------------+
|  MULTI-TF SCANNER (Interactive & Auto-Stream)         |
+-------------------------------------------------------+
{rows_joined}
+-------------------------------------------------------+
| MODE          : {mode:<37} |
| ACTIVE TF     : {active_tf:<37} |
| BTC PRICE     : ${display_price:,.2f}                     |
| FADE-SHORT SL : ${display_price * 1.002:,.2f}               |
| SIZE (BTC)    : 0.0360                                |
| SIZE (USD)    : ${display_price * 0.0360:,.2f}                |
| CONDITION     : MACRO COMPRESSION ({active_tf})                 |
| STRATEGY      : {strategy:<37} |
+-------------------------------------------------------+
| LAST SYNC     : {current_time} | Status: LIVE KRAKEN  |
+-------------------------------------------------------+"""

  st.markdown(f"```text\n{terminal_display}\n```")


# Run the live fragment block passing the sidebar settings
render_live_scanner(selected_tf, selected_mode)
