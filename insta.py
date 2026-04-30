import requests
import time
import os
from datetime import datetime, timedelta

# 🔐 TOKENS
API_TOKEN = os.getenv("APIFY_TOKEN", "APIFY_TOKEN_AQUI")
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "NOTION_TOKEN_AQUI")
DATABASE_ID = os.getenv("DATABASE_ID", "DATABASE_ID_AQUI")

APIFY_URL = f"https://api.apify.com/v2/acts/apify~instagram-scraper/run-sync-get-dataset-items?token={API_TOKEN}"

VIRAL_THRESHOLD = 0.05
CHECK_INTERVAL = 600  # 10 minutos


def get_posts():
    data = {
        "directUrls": [
            "https://www.instagram.com/acknowledge.ai/",
            "https://www.instagram.com/ecoeconomiaonline/",
            "https://www.instagram.com/bloombergbusiness/"
        ],
        "resultsLimit": 50
    }

    try:
        res = requests.post(APIFY_URL, json=data)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("❌ erro na API:", e)
        return []


def get_existing_post_ids():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    ids = set()

    try:
        res = requests.post(url, headers=headers)
        data = res.json()

        for page in data.get("results", []):
            props = page.get("properties", {})
            post_id = props.get("Post ID", {}).get("rich_text", [])

            if post_id:
                ids.add(post_id[0]["text"]["content"])

    except Exception as e:
        print("❌ erro a ler Notion:", e)

    return ids


# 📤 enviar para Notion
def send_to_notion(post_id, profile, likes, comments, ratio, link):
    url = "https://api.notion.com/v1/pages"

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Post": {
                "title": [{"text": {"content": profile}}]
            },
            "Post ID": {
                "rich_text": [{"text": {"content": post_id}}]
            },
            "Likes": {"number": likes},
            "Comments": {"number": comments},
            "Score": {"number": ratio},
            "Link": {"url": link}
        }
    }

    res = requests.post(url, headers=headers, json=data)

    if res.status_code != 200:
        print("❌ Erro Notion:", res.text)


# 🔥 scanner principal
def scan():
    print("🚀 Scanner Instagram\n")

    posts = get_posts()
    if not posts:
        print("❌ Nenhum post encontrado")
        return

    existing_ids = get_existing_post_ids()

    four_days_ago = datetime.now() - timedelta(days=4)

    for p in posts:
        post_id = p.get("id") or p.get("shortCode")
        if not post_id:
            continue

        if post_id in existing_ids:
            continue  # 🚫 evita duplicados

        timestamp = p.get("timestamp")
        if not timestamp:
            continue

        try:
            post_date = datetime.fromisoformat(timestamp.replace("Z", ""))
        except:
            continue

        if post_date < four_days_ago:
            continue

        likes = p.get("likesCount", 0)
        comments = p.get("commentsCount", 0)

        ratio = (likes + comments) / 1000

        if ratio > VIRAL_THRESHOLD:
            send_to_notion(
                post_id,
                p.get("ownerUsername", "desconhecido"),
                likes,
                comments,
                round(ratio, 3),
                p.get("url")
            )

            print("🔥 NOVO POST VIRAL:", p.get("url"))
            time.sleep(0.5)


def run_forever():
    while True:
        try:
            scan()
        except Exception as e:
            print("❌ erro geral:", e)

        print(f"⏳ A aguardar {CHECK_INTERVAL/60} minutos...\n")
        time.sleep(CHECK_INTERVAL)


run_forever()
