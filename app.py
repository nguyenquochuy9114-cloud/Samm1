import streamlit as st
import requests
import pandas as pd
import numpy as np
import datetime
from datetime import datetime, timedelta

# -------------------------
# Hàm lấy dữ liệu coin từ API CoinGecko
# -------------------------
def get_coin_data(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&community_data=false&developer_data=false&sparkline=false"
    response = requests.get(url)
    data = response.json()

    market_data = data.get("market_data", {})

    return {
        "name": data["name"],
        "symbol": data["symbol"].upper(),
        "price": market_data.get("current_price", {}).get("usd"),
        "market_cap": market_data.get("market_cap", {}).get("usd"),
        "volume": market_data.get("total_volume", {}).get("usd"),
        "market_cap_change_percentage_30d": market_data.get("market_cap_change_percentage_30d"),
        "rsi": None  # sẽ tính sau
    }

# -------------------------
# Hàm lấy dữ liệu lịch sử giá để tính RSI
# -------------------------
def get_historical_data(coin_id, days=90):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
    response = requests.get(url)
    data = response.json()
    prices = data["prices"]

    df = pd.DataFrame(prices, columns=["time", "price"])
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    return df

# -------------------------
# Hàm tính RSI
# -------------------------
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# -------------------------
# Main App
# -------------------------
def main():
    st.set_page_config(page_title="Crypto Analyzer App", layout="wide")
    st.title("📊 Crypto Analyzer App")
    st.write("Phân tích giá, khối lượng & gợi ý điểm vào lệnh bằng RSI")

    # Coin mặc định
    selected_coin = st.selectbox("Chọn coin:", ["bitcoin", "ethereum", "binancecoin", "solana", "ripple"])

    # Lấy dữ liệu coin
    coin_data = get_coin_data(selected_coin)

    # Phân tích thị trường
    if coin_data["price"] and coin_data["market_cap"]:
        st.subheader(f"📌 Phân tích {coin_data['name'].upper()} ({datetime.today().strftime('%Y-%m-%d')})")

        st.write(f"💰 Giá hiện tại: **${coin_data['price']:,}**")
        st.write(f"🏦 Market Cap hiện tại: **${coin_data['market_cap']:,}**")

        # % thay đổi Market Cap trong 30 ngày
        change_30d = coin_data.get("market_cap_change_percentage_30d", None)
        if change_30d:
            st.write(f"% Thay đổi Market Cap (30 ngày): **{round(change_30d, 2)}%**")

        # Tỷ lệ volume
        if coin_data["volume"] and coin_data["market_cap"]:
            vol_ratio = coin_data["volume"] / coin_data["market_cap"]
            st.write(f"Tỷ lệ Volume (24h / MarketCap): **{round(vol_ratio, 2)}**")

        # Proxy dòng tiền
        if coin_data["volume"]:
            st.write(f"Dòng tiền (Inflow proxy): **${coin_data['volume']:,}**")

    # Lấy dữ liệu lịch sử để tính RSI
    df = get_historical_data(selected_coin, days=90)
    df["RSI"] = calculate_rsi(df["price"])
    coin_data["rsi"] = df["RSI"].iloc[-1]

    # Hiển thị RSI & tín hiệu Trade
    st.write(f"RSI (14): **{round(coin_data['rsi'], 2)}**")

    if coin_data["rsi"] < 30:
        st.success("📈 Tín hiệu Trade: Mua")
    elif coin_data["rsi"] > 70:
        st.error("📉 Tín hiệu Trade: Bán")
    else:
        st.info("⏸️ Tín hiệu Trade: Giữ")

    # Biểu đồ
    st.subheader("📊 Biểu đồ kỹ thuật")
    st.line_chart(df.set_index("time")[["price", "RSI"]])

    # Bảng gợi ý tín hiệu RSI
    st.subheader("📌 Gợi ý tín hiệu (RSI)")
    df_table = df[["time", "price", "RSI"]].tail(50).copy()
    df_table["Signal"] = df_table["RSI"].apply(lambda x: "Mua" if x < 30 else ("Bán" if x > 70 else "Giữ"))
    st.dataframe(df_table)

# -------------------------
if __name__ == "__main__":
    main()
