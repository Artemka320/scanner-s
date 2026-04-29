import requests
from datetime import datetime, timedelta
import time

# 🔐 CONFIG
API_KEY = "apify_api_ZEG61KfKbxU9peHKB2L0ADw7lXJ6bQ4qFQnY"
DATABASE_ID = "32d1aebf9259809b98c1e87fc7e66d39"
NOTION_TOKEN = "ntn_u72267577213OBPMFlQFK85T9P1j30rp2EN5NoFBCd09QO"

headers_notion = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

VIRAL_THRESHOLD = 0.15

# 🔹 enviar para notion
def add_to_notion(creator, followers, views, likes, link):
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Vídeo": {"title": [{"text": {"content": creator}}]},
            "Followers": {"number": followers},
            "Views": {"number": views},
            "Likes": {"number": likes},
            "Link": {"url": link}
        }
    }

    res = requests.post(
        "https://api.notion.com/v1/pages",
        headers=headers_notion,
        json=data,
        timeout=30
    )

    if res.status_code not in [200, 201]:
        print("❌ Notion erro:", res.text)
    else:
        print("✅ Enviado")


# 🔹 APIFY
def get_videos(profile_url):
    url = f"https://api.apify.com/v2/acts/clockworks~tiktok-scraper/run-sync-get-dataset-items?token={API_KEY}"

    payload = {
        "profiles": [profile_url],
        "resultsPerPage": 10
    }

    res = requests.post(url, json=payload, timeout=30)
    res.raise_for_status()

    return res.json()


# 🔹 scanner
def scan():
    print("🚀 Scanner API TikTok\n")

    profiles = [
        "https://www.tiktok.com/@theventureroom",
        "https://www.tiktok.com/@bloombergbusiness"
    ]

    four_days_ago = datetime.now() - timedelta(days=4)

    for profile in profiles:
        try:
            videos = get_videos(profile)
            username = profile.split("@")[-1]

            for v in videos:
                create_time = v.get("createTime", 0)
                video_date = datetime.fromtimestamp(create_time)

                if video_date < four_days_ago:
                    continue

                views = v.get("playCount", 0)
                likes = v.get("diggCount", 0)
                followers = v.get("authorStats", {}).get("followerCount", 1)

                link = v.get("webVideoUrl")

                ratio = views / followers if followers > 0 else 0

                if ratio > VIRAL_THRESHOLD:
                    add_to_notion(username, followers, views, likes, link)

                    print("🔥 VIRAL:", username, views, likes)

                    time.sleep(1)

        except Exception as e:
            print("❌ erro:", profile, e)


scan()