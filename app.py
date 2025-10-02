import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
from datetime import datetime

# ==============================
# Load danh sách coin từ coins.json
# ==============================
def load_coins():
    with open("coins.json", "r", encoding="utf-8") as f:
        return json.load(f)

# ==============================
# Hàm lấy dữ liệu thị trường từ CoinGecko
# ==============================
@st.cache_data(ttl=60)  # cache trong 60 giây
def fetch_market_chart(coin_id, days=30, vs_currency="usd"):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': vs_currency,
        'days': days,
        'interval': 'daily'
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# ==============================
# Tính RSI
# ==============================
def calculate_rsi(prices, period=14):
    deltas = np.diff(prices)
    seed = deltas[:period]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)

    for i in range(period, len(prices)):
        delta = deltas[i - 1]
        if delta > 0:
            upval, downval = delta, 0.
        else:
            upval, downval = 0., -delta

        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        rs = up / down if down != 0 else 0
        rsi[i] = 100. - 100. / (1. + rs)
    return rsi

# ==============================
# App chính
# ==============================
def main():
    st.title("📊 Crypto Analyzer App")
    st.write("Phân tích giá, khối lượng & gợi ý điểm vào lệnh bằng RSI")

    coins = load_coins()
    coin_names = [c["id"] for c in coins]

    st.sidebar.header("⚙️ Tùy chỉnh")
    coin = st.sidebar.selectbox("Chọn coin", coin_names, index=0)
    days = st.sidebar.slider("Số ngày phân tích", 30, 180, 60)

    data = fetch_market_chart(coin, days=days)
    if not data:
        st.error("Không lấy được dữ liệu (API limit hoặc coin sai).")
        return

    prices = [p[1] for p in data['prices']]
    times = [datetime.fromtimestamp(p[0] / 1000) for p in data['prices']]
    volumes = [v[1] for v in data['total_volumes']]

    df = pd.DataFrame({"time": times, "price": prices, "volume": volumes})
    df["RSI"] = calculate_rsi(df["price"].values)

    # Vẽ biểu đồ giá
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(df["time"], df["price"], label="Price", color="blue")
    ax1.set_ylabel("Price (USD)")
    ax2 = ax1.twinx()
    ax2.bar(df["time"], df["volume"], alpha=0.3, color="gray", label="Volume")
    ax2.set_ylabel("Volume")
    plt.title(f"{coin.upper()} Price & Volume")
    st.pyplot(fig)

    # Bảng tín hiệu vào lệnh
    st.subheader("📌 Gợi ý tín hiệu (RSI)")
    signals = []
    for i in range(len(df)):
        rsi = df["RSI"].iloc[i]
        signal = "Giữ"
        if rsi < 30:
            signal = "Mua (Oversold)"
        elif rsi > 70:
            signal = "Bán (Overbought)"
        signals.append(signal)

    df["Signal"] = signals
    st.dataframe(df[["time", "price", "RSI", "Signal"]].tail(20))

if __name__ == "__main__":
    main()
