import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import json

# ==============================
# Lấy dữ liệu từ CoinGecko API
# ==============================
def fetch_market_chart(coin_id, days=30, vs_currency='usd'):
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
        st.error(f"Error fetching data: {response.status_code}")
        return None

# ==============================
# Load danh sách coin từ file JSON
# ==============================
@st.cache_data
def load_coin_list():
    with open("coins.json", "r", encoding="utf-8") as f:
        coins = json.load(f)
    return {f"{c['name']} ({c['symbol'].upper()})": c['id'] for c in coins}

# ==============================
# Tính toán các chỉ báo
# ==============================
def calculate_metrics(data, days=30):
    if not data:
        return None

    timestamps = [p[0] for p in data['prices']]
    prices = [p[1] for p in data['prices']]
    market_caps = [mc[1] for mc in data['market_caps']]
    volumes = [v[1] for v in data['total_volumes']]

    df = pd.DataFrame({
        'timestamp': pd.to_datetime(timestamps, unit='ms'),
        'price': prices,
        'market_cap': market_caps,
        'volume': volumes
    })

    mc_change_pct = ((df['market_cap'].iloc[-1] - df['market_cap'].iloc[0]) / df['market_cap'].iloc[0]) * 100
    vol_7d = df['volume'].tail(min(7, len(df))).sum()
    vol_full = df['volume'].sum()
    vol_ratio = vol_7d / vol_full if vol_full > 0 else 0
    df['price_change_pct'] = df['price'].pct_change() * 100
    money_flow = (df['volume'] * df['price_change_pct']).sum()

    def calculate_rsi(prices, period=14):
        delta = pd.Series(prices).diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    rsi_series = calculate_rsi(prices)
    rsi_val = rsi_series.iloc[-1] if len(rsi_series) > 0 and not pd.isna(rsi_series.iloc[-1]) else 50
    signal = 'Buy' if rsi_val < 30 else 'Sell' if rsi_val > 70 else 'Hold'

    return {
        'df': df,
        'mc_change_pct': mc_change_pct,
        'vol_ratio': vol_ratio,
        'money_flow': money_flow,
        'rsi': rsi_val,
        'signal': signal,
        'current_price': prices[-1],
        'current_mc': market_caps[-1],
        'period_days': days
    }

# ==============================
# Streamlit UI
# ==============================
def main():
    st.title("📊 Crypto Analyzer App")
    st.write("Phân tích dòng tiền, khối lượng giao dịch & tín hiệu trade từ CoinGecko API")

    st.sidebar.header("⚙️ Tùy chỉnh")
    coin_dict = load_coin_list()
    coin_name = st.sidebar.selectbox("Chọn coin", list(coin_dict.keys()))
    coin_id = coin_dict[coin_name]
    days = st.sidebar.slider("Số ngày phân tích", 7, 90, 30)

    data = fetch_market_chart(coin_id, days)
    metrics = calculate_metrics(data, days)

    if metrics:
        st.subheader(f"📌 Phân tích {coin_name} ({datetime.now().strftime('%Y-%m-%d')})")
        st.metric("💰 Giá hiện tại", f"${metrics['current_price']:,.2f}")
        st.metric("📉 Market Cap hiện tại", f"${metrics['current_mc']:,.0f}")
        st.write(f"**% Thay đổi Market Cap ({days} ngày):** {metrics['mc_change_pct']:.2f}%")
        st.write(f"**Tỷ lệ Volume (7d / {days}d):** {metrics['vol_ratio']:.2f}")
        st.write(f"**Dòng tiền (Inflow proxy):** ${metrics['money_flow']:,.0f}")
        st.write(f"**RSI (14):** {metrics['rsi']:.2f}")
        st.success(f"📈 Tín hiệu Trade: {metrics['signal']}")

        st.subheader("📊 Biểu đồ kỹ thuật")
        df = metrics['df']
        fig, ax1 = plt.subplots(figsize=(10,5))
        ax1.plot(df['timestamp'], df['price'], color='blue', label="Price")
        ax1.set_ylabel("Price (USD)", color='blue')
        ax1.tick_params(axis='y', labelcolor='blue')

        ax2 = ax1.twinx()
        ax2.bar(df['timestamp'], df['volume'], alpha=0.3, color='orange', label="Volume")
        ax2.set_ylabel("Volume", color='orange')
        ax2.tick_params(axis='y', labelcolor='orange')

        plt.title(f"{coin_name} - Price & Volume")
        st.pyplot(fig)

if __name__ == "__main__":
    main()
