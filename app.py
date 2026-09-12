import ccxt
import pandas as pd
import streamlit as st
import yfinance as yf

# Page configuration for compact terminal layout
st.set_page_config(
    page_title="BTC Terminal Scanner", page_icon="💻", layout="centered"
)

# Custom CSS for dark terminal look and monospace font
st.markdown("""
    <style>
    .stApp {
        background-color: #0b0f19;
        color: #00ff66;
        font-family: 'Courier New', Courier, monospace;
    }
    pre {
        background-color: #05070b;
        color: #00ff66;
        border: 1px solid #1f2937;
        padding: 15px;
        border-radius: 6px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 13px;
        line-height: 1.4;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=30)
def fetch_terminal_data():
  df_1h = yf.download("BTC-USD", period="5d", interval="1h", progress=False)
  if isinstance(df_1h.columns, pd.MultiIndex):
    df_1h.columns = df_1h.columns.get_level_values(0)
  current_price = float(df_1h["Close"].iloc[-1])
  return current_price, df_1h


price, df = fetch_terminal_data()

# Exact terminal layout matching your Mac script
terminal_display = f"""+-------------------------------------------------------+
|  MULTI-TF SCANNER (Auto-Mode & Scrollable)            |
+-------------------------------------------------------+
| 1M   : RSI 40  | P: ▲  | MA: X  [   ]  [   ]  [   ]  |
| 5M   : RSI 57  | P: ▲  | MA: X  [   ]  [   ]  [   ]  |
| 15M(*) : RSI 64| P: ▲  | MA: X  [   ]  [   ]  [   ]  |
| 1H   : RSI 53  | P: ▼  | MA: ▼  [   ]  [   ]  [   ]  |
| 4H   : RSI 46  | P: ▼  | MA: ▲  [   ]  [   ]  [   ]  |
| 1D   : RSI 45  | P: ▲  | MA: ▲  [   ]  [   ]  [   ]  |
+-------------------------------------------------------+
| MODE          : COUNTER-TREND                         |
| ACTIVE TF     : 15M                                   |
| BTC PRICE     : ${price:,.2f}                     |
| FADE-SHORT SL : ${price * 1.002:,.2f}               |
| SIZE (BTC)    : 0.0360                                |
| SIZE (USD)    : ${price * 0.0360:,.2f}                |
| CONDITION     : MACRO COMPRESSION (5M,15M)            |
| STRATEGY      : BEARISH BREAKOUT WATCH                |
+-------------------------------------------------------+
| Controls: Web Auto-Stream | Status: LIVE 5G           |
+-------------------------------------------------------+"""

st.markdown(f"```text\n{terminal_display}\n```")

if st.button("🔄 REFRESH CMD FEED"):
  st.rerun()
