import requests
import time
from datetime import datetime, timedelta
from openpyxl import Workbook

print("🚀 LINKEDIN ")

# 🔹 Excel
wb = Workbook()
ws = wb.active
ws.title = "LinkedIn Virais"

ws.append(["Profile", "Text", "Likes", "Comments", "Views", "Score", "Link"])

# 🔐 token
API_TOKEN = "apify_api_ZEG61KfKbxU9peHKB2L0ADw7lXJ6bQ4qFQnY"

# ✅ actor
url = f"https://api.apify.com/v2/acts/supreme_coder~linkedin-post/run-sync-get-dataset-items?token={API_TOKEN}"

RESULTS_LIMIT = 20
DELAY = 1
VIRAL_THRESHOLD = 0.02


def get_posts():
    data = {
        "urls": [
            "https://www.linkedin.com/company/bloomberg/",
        ],
        "resultsLimit": RESULTS_LIMIT
    }

    try:
        print("🔗 URL:", url)

        res = requests.post(url, json=data)

        print("STATUS:", res.status_code)
        print("DEBUG:", res.text[:200])

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


def scan():
    posts = get_posts()

    if not posts:
        print("❌ Nenhum post encontrado")
        return

    four_days_ago = datetime.now() - timedelta(days=4)

    for p in posts:

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

        text = p.get("text", "")[:100]
        link = p.get("url") or p.get("postUrl") or ""

        likes = p.get("likesCount") or p.get("reactionCount") or 0
        comments = p.get("commentsCount") or p.get("commentCount") or 0
        views = p.get("viewsCount") or p.get("viewCount") or 0

        score = (likes * 1 + comments * 4)

        if views > 0:
            ratio = score / views
        else:
            ratio = score / 1000

        # 🔥 FORMATAÇÃO BONITA
        print("\n💼 POST")
        print(f"👤 Perfil: {profile}")
        print(f"❤️ Likes: {likes}")
        print(f"💬 Comentários: {comments}")
        print(f"👀 Views: {views}")
        print(f"🔗 Link: {link}")
        print("━━━━━━━━━━━━━━━━")

        if ratio > VIRAL_THRESHOLD:

            ws.append([
                profile,
                text,
                likes,
                comments,
                views,
                round(ratio, 4),
                link
            ])

            time.sleep(DELAY)

    wb.save("linkedin_posts.xlsx")


scan()

print("✅ Excel guardado!")
