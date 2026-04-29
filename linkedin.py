import requests
import time
from datetime import datetime, timedelta
import json

print("🚀 LINKEDIN")

# 🔐 APIFY
API_TOKEN = "apify_api_ZEG61KfKbxU9peHKB2L0ADw7lXJ6bQ4qFQnY"

url = f"https://api.apify.com/v2/acts/supreme_coder~linkedin-post/run-sync-get-dataset-items?token={API_TOKEN}"

RESULTS_LIMIT = 20
DELAY = 1
VIRAL_THRESHOLD = 0.02

# 🔐 NOTION (⚠️ mantém os teus valores aqui)
DATABASE_ID = "32d1aebf9259809b98c1e87fc7e66d39"
NOTION_TOKEN = "ntn_u72267577213OBPMFlQFK85T9P1j30rp2EN5NoFBCd09QO"

NOTION_URL = "https://api.notion.com/v1/pages"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}


# 🔥 ENVIAR PARA NOTION
def send_to_notion(profile, text, likes, comments, views, score, link):
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Profile": {
                "title": [
                    {"text": {"content": profile}}
                ]
            },
            "Text": {
                "rich_text": [
                    {"text": {"content": text}}
                ]
            },
            "Likes": {"number": likes},
            "Comments": {"number": comments},
            "Views": {"number": views},
            "Score": {"number": score},
            "Link": {"url": link}
        }
    }

    res = requests.post(NOTION_URL, headers=headers, json=data, timeout=30)

    if res.status_code not in [200, 201]:
        print("❌ Erro Notion:", res.text)
    else:
        print("✅ Enviado para Notion!")


def get_posts():
    data = {
        "urls": [
            "https://www.linkedin.com/company/bloomberg/"
        ],
        "resultsLimit": RESULTS_LIMIT
    }

    try:
        res = requests.post(url, json=data, timeout=30)

        print("DEBUG:", res.text[:200])  # preview resposta

        res.raise_for_status()
        return res.json()

    except Exception as e:
        print("❌ erro:", e)
        return []


def parse_date(p):
    date_str = (
        p.get("postedAt")
        or p.get("createdAt")
        or p.get("time")
    )

    if not date_str:
        return datetime.now()

    try:
        return datetime.fromisoformat(date_str.replace("Z", ""))
    except:
        return datetime.now()


def extract_link(p):
    # 🔥 tenta vários campos possíveis
    for key in ["url", "postUrl", "activityUrl", "permalink"]:
        if p.get(key):
            return p.get(key)

    return ""


def scan():
    posts = get_posts()

    if not posts:
        print("❌ Nenhum post encontrado")
        return

    four_days_ago = datetime.now() - timedelta(days=4)

    for p in posts:

        # DEBUG profundo (descomenta se precisares)
        # print(json.dumps(p, indent=2))

        if p.get("isActivity") == True:
            continue

        post_date = parse_date(p)

        if post_date < four_days_ago:
            continue

        profile = (
            p.get("authorName")
            or p.get("actorName")
            or "desconhecido"
        )

        text = (p.get("text") or "")[:100]

        # 🔥 LINK CORRIGIDO
        link = extract_link(p)

        likes = p.get("likesCount") or p.get("reactionCount") or 0
        comments = p.get("commentsCount") or p.get("commentCount") or 0
        views = p.get("viewsCount") or p.get("viewCount") or 0

        score = (likes * 1 + comments * 4)

        if views > 0:
            ratio = score / views
        else:
            ratio = score / 1000

        print("\n💼 POST")
        print("Perfil:", profile)
        print("Likes:", likes)
        print("Comments:", comments)
        print("Views:", views)
        print("Link:", link)

        if ratio > VIRAL_THRESHOLD:

            print("🔥 VIRAL → ENVIAR PARA NOTION")

            send_to_notion(
                profile,
                text,
                likes,
                comments,
                views,
                round(ratio, 4),
                link
            )

            time.sleep(DELAY)


# 🚀 RUN
scan()