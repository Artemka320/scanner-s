import requests
import time
import os
from datetime import datetime, timedelta

# 🔐 TOKENS
API_TOKEN = os.getenv("APIFY_TOKEN")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")

APIFY_URL = f"https://api.apify.com/v2/acts/apify~instagram-scraper/run-sync-get-dataset-items?token={API_TOKEN}"

VIRAL_THRESHOLD = 0.05
CHECK_INTERVAL = 600  # 10 minutos


# 🔍 buscar posts
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


# 🔍 posts já guardados
def get_existing_ids():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28"
    }

    ids = set()

    try:
        res = requests.post(url, headers=headers)
        data = res.json()

        for page in data.get("results", []):
            prop = page["properties"].get("Post ID", {})
            txt = prop.get("rich_text", [])

            if txt:
                ids.add(txt[0]["text"]["content"])

    except Exception as e:
        print("❌ erro ao ler Notion:", e)

    return ids


# 📤 enviar para Notion
def send_to_notion(post_id, profile, likes, comments, ratio, link, image, caption):
    url = "https://api.notion.com/v1/pages"

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    files = []
    if image:
        files = [{
            "name": "post_image",
            "external": {"url": image}
        }]

    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Post": {
                "title": [{"text": {"content": profile or "sem nome"}}]
            },
            "Post ID": {
                "rich_text": [{"text": {"content": post_id}}]
            },
            "Likes": {"number": likes},
            "Comments": {"number": comments},
            "Score": {"number": ratio},
            "Link": {"url": link},
            "Caption": {
                "rich_text": [{"text": {"content": caption[:2000] if caption else ""}}]
            },
            "Image": {
                "files": files
            }
        }
    }

    res = requests.post(url, headers=headers, json=data)

    if res.status_code != 200:
        print("❌ Notion erro:", res.text)


# 🔥 scanner
def scan():
    print("🚀 scanning...")

    posts = get_posts()
    if not posts:
        return

    existing_ids = get_existing_ids()
    four_days_ago = datetime.now() - timedelta(days=4)

    for p in posts:
        post_id = p.get("id") or p.get("shortCode")
        if not post_id or post_id in existing_ids:
            continue

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
            image = (
                p.get("displayUrl")
                or p.get("imageUrl")
                or p.get("thumbnailUrl")
                or p.get("videoThumbnail")
            )

            caption = p.get("caption", "")

            send_to_notion(
                post_id,
                p.get("ownerUsername"),
                likes,
                comments,
                round(ratio, 3),
                p.get("url"),
                image,
                caption
            )

            print("🔥 novo viral:", p.get("url"))
            time.sleep(0.5)


# 🔁 loop automático
def run():
    while True:
        try:
            scan()
        except Exception as e:
            print("❌ erro:", e)

        print(f"⏳ esperar {CHECK_INTERVAL/60} min\n")
        time.sleep(CHECK_INTERVAL)


run()
