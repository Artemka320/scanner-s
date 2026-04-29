import requests
import time
import os
from datetime import datetime, timedelta
from openpyxl import Workbook  # ✅ precisa do openpyxl instalado

# 🔹 criar Excel
wb = Workbook()
ws = wb.active
ws.title = "Posts Virais"

ws.append(["Profile", "Likes", "Comments", "Ratio", "Link"])

API_TOKEN = os.getenv("APIFY_TOKEN", "apify_api_ZEG61KfKbxU9peHKB2L0ADw7lXJ6bQ4qFQnY")

RESULTS_PER_PAGE = 50
DELAY = 0.5
VIRAL_THRESHOLD = 0.05

url = f"https://api.apify.com/v2/acts/apify~instagram-scraper/run-sync-get-dataset-items?token={API_TOKEN}"


def get_posts():
    data = {
        "directUrls": [
            "https://www.instagram.com/acknowledge.ai/",
            "https://www.instagram.com/ecoeconomiaonline/",
            "https://www.instagram.com/bloombergbusiness/"
        ],
        "resultsLimit": RESULTS_PER_PAGE
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


def scan():
    print("🚀 Scanner Instagram\n")

    posts = get_posts()

    if not posts:
        print("❌ Nenhum post encontrado")
        return

    # 🔥 últimos 4 dias
    four_days_ago = datetime.now() - timedelta(days=4)

    for p in posts:
        timestamp = p.get("timestamp")
        if not timestamp:
            continue

        # ✅ proteção contra erro de formato de data
        try:
            post_date = datetime.fromisoformat(timestamp.replace("Z", ""))
        except Exception:
            continue

        if post_date < four_days_ago:
            continue

        profile = p.get("ownerUsername", "desconhecido")
        link = p.get("url", "")

        likes = p.get("likesCount", 0)
        comments = p.get("commentsCount", 0)

        # 🔥 cálculo de viralidade
        ratio = (likes + comments) / 1000

        if ratio > VIRAL_THRESHOLD:
            ws.append([
                profile,
                likes,
                comments,
                round(ratio, 3),
                f'=HYPERLINK("{link}", "Ver post")'
            ])

            # 💾 guarda sempre o Excel atualizado
            wb.save("instagram_posts.xlsx")

            print("🔥 POST VIRAL (últimos 4 dias)")
            print("━━━━━━━━━━━━━━━━")
            print("Perfil:", profile)
            print("Likes:", likes)
            print("Comentários:", comments)
            print("Score:", round(ratio, 2))
            print("Link:", link)
            print()

            time.sleep(DELAY)


# 🔹 executar
scan()

print("✅ Excel atualizado em tempo real!")