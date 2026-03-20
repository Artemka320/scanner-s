import requests
import time
import os
from datetime import datetime, timedelta
from openpyxl import Workbook

# 🔹 criar Excel
wb = Workbook()
ws = wb.active
ws.title = "Videos Virais"

# cabeçalhos
ws.append(["Creator", "Followers", "Views", "Likes", "Ratio", "Link"])

API_TOKEN = os.getenv("APIFY_TOKEN", "apify_api_xeLLSxvi4IIcjhIRWkZzEGEQhbNNz83pGeVa")

RESULTS_PER_PAGE = 50
DELAY = 1
VIRAL_THRESHOLD = 0.15  # 15%

url = f"https://api.apify.com/v2/acts/clockworks~tiktok-scraper/run-sync-get-dataset-items?token={API_TOKEN}"

def get_videos():
    data = {
        "profiles": [
            "https://www.tiktok.com/@steven",
            "https://www.tiktok.com/@theventureroom",
            "https://www.tiktok.com/@bloombergbusiness"
        ],
        "resultsPerPage": RESULTS_PER_PAGE
    }

    try:
        res = requests.post(url, json=data)
        print("DEBUG:", res.text[:200])

        res.raise_for_status()
        result = res.json()

        if isinstance(result, list):
            return result

        if isinstance(result, dict) and "data" in result:
            return result["data"]

        return []

    except Exception as e:
        print("❌ erro na API:", e)
        return []

def get_followers(author):
    if not isinstance(author, dict):
        return 0

    for key in ["fans", "followers", "followerCount", "fansCount"]:
        val = author.get(key)
        if isinstance(val, int):
            return val

    return 0

def scan():
    print("🚀 Scanner TikTok\n")

    videos = get_videos()

    if not videos:
        print("❌ Nenhum vídeo encontrado")
        return

    # 🔥 últimos 4 dias
    four_days_ago = datetime.now() - timedelta(days=4)

    for v in videos:

        # 🔹 filtrar por data
        create_time = v.get("createTime")
        if not create_time:
            continue

        video_date = datetime.fromtimestamp(create_time)

        if video_date < four_days_ago:
            continue

        author = v.get("authorMeta", {})
        creator = author.get("name") or author.get("nickName") or "desconhecido"

        views = v.get("playCount", 0)
        likes = v.get("diggCount", 0)
        link = v.get("webVideoUrl", "")

        followers = get_followers(author)

        if followers == 0:
            continue

        ratio = views / followers

        if ratio > VIRAL_THRESHOLD:

            # 🔥 guardar no Excel
            ws.append([creator, followers, views, likes, ratio, link])

            print("🔥 VIDEO VIRAL (últimos 4 dias)")
            print("━━━━━━━━━━━━━━━━")
            print("Creator:", creator)
            print("Followers:", followers)
            print("Views:", views)
            print("Likes:", likes)
            print("Percentagem de viralização:", round(ratio * 100, 2), "%")
            print("Link:", link)
            print()

            time.sleep(DELAY)

# 🔹 executar
scan()

# 🔹 guardar Excel
wb.save("videos.xlsx")
print("✅ Excel guardado!")