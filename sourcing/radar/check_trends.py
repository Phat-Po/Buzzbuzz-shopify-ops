"""驗證信號 A：用 SerpAPI 查 Google Trends（台灣地區）搜尋熱度。

用法：
    python3 sourcing/radar/check_trends.py "KICHIZO" "Helinox" "LOGOS" "Converse Tokyo" "Twinbird"

輸出每個關鍵詞近 12 個月在台灣地區的平均/最高搜尋熱度指數（0-100，Google Trends 相對值，
不是絕對搜尋量）。平均值 >=5 視為有基本搜尋基線，命中信號 A。
"""

import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("SERPAPI_KEY")
ENDPOINT = "https://serpapi.com/search"


def check_trend(keyword: str) -> dict:
    params = {
        "engine": "google_trends",
        "q": keyword,
        "geo": "TW",
        "date": "today 12-m",
        "api_key": API_KEY,
    }
    resp = requests.get(ENDPOINT, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    timeline = data.get("interest_over_time", {}).get("timeline_data", [])
    values = []
    for point in timeline:
        for v in point.get("values", []):
            values.append(v.get("extracted_value", 0))

    if not values:
        return {"keyword": keyword, "avg": 0, "max": 0, "signal_a": False, "note": "無資料"}

    avg = sum(values) / len(values)
    peak = max(values)
    return {
        "keyword": keyword,
        "avg": round(avg, 1),
        "max": peak,
        "signal_a": avg >= 5,
        "note": "",
    }


def main():
    keywords = sys.argv[1:]
    if not keywords:
        print("請提供至少一個關鍵詞")
        sys.exit(1)
    if not API_KEY:
        print("錯誤：.env 裡沒有 SERPAPI_KEY")
        sys.exit(1)

    print(f"{'關鍵詞':<24}{'平均熱度':<10}{'峰值':<8}{'信號A':<8}")
    for kw in keywords:
        r = check_trend(kw)
        hit = "命中" if r["signal_a"] else "未命中"
        print(f"{r['keyword']:<24}{r['avg']:<10}{r['max']:<8}{hit:<8}")


if __name__ == "__main__":
    main()
