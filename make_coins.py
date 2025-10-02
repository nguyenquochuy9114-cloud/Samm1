import requests
import json

def fetch_top_coins(total=500, currency="usd", file_name="coins.json"):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    per_page = 250
    pages = (total // per_page) + (1 if total % per_page != 0 else 0)

    coins_list = []

    print(f"🔄 Đang tải {total} coin từ CoinGecko...")

    for page in range(1, pages + 1):
        params = {
            "vs_currency": currency,
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": page,
            "sparkline": "false"
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            coins_data = response.json()
            coins_page = [
                {"id": coin["id"], "symbol": coin["symbol"], "name": coin["name"]}
                for coin in coins_data
            ]
            coins_list.extend(coins_page)
            print(f"✅ Trang {page} tải được {len(coins_page)} coin")
        else:
            print(f"❌ Lỗi khi gọi API (trang {page}): {response.status_code}")

    # Giới hạn số lượng theo yêu cầu
    coins_list = coins_list[:total]

    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(coins_list, f, indent=2, ensure_ascii=False)

    print(f"\n🎉 Hoàn tất! Đã lưu {len(coins_list)} coin vào {file_name}")

if __name__ == "__main__":
    fetch_top_coins(total=500)
