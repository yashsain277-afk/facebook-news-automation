import json
import os
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone

from news_collector import collect_all_news, remove_duplicates, normalize_title
from janta_ki_awaz_frame import make_frame

PAGE_ID = os.environ["JANTA_KI_AWAZ_PAGE_ID"]
ACCESS_TOKEN = os.environ["JANTA_KI_AWAZ_PAGE_ACCESS_TOKEN"]
POSTED_FILE = "janta_ki_awaz_posted.json"
IST = timezone(timedelta(hours=5, minutes=30))


def load_posted():
    try:
        with open(POSTED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_posted(items):
    with open(POSTED_FILE, "w", encoding="utf-8") as f:
        json.dump(items[-200:], f, ensure_ascii=False, indent=2)


def post_photo(image_path, caption):
    url = f"https://graph.facebook.com/v26.0/{PAGE_ID}/photos"
    boundary = uuid.uuid4().hex
    with open(image_path, "rb") as f:
        image_data = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="caption"\r\n\r\n'
        f"{caption}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="access_token"\r\n\r\n'
        f"{ACCESS_TOKEN}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="source"; filename="janta_ki_awaz.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8")
    body += image_data
    body += f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def main():
    posted = load_posted()
    posted_links = {x.get("link") for x in posted if isinstance(x, dict)}

    all_news = remove_duplicates(collect_all_news())

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=6)

    candidates = []
    for item in all_news:
        link = item.get("link", "")
        published = item.get("published")
        if not link or link in posted_links or not published:
            continue
        if published < cutoff:
            continue

        # Keep this workflow focused on the local area.
        category = item.get("category", "")
        if category not in {"Anta", "Baran", "Baran District", "Rajasthan Local"}:
            continue

        candidates.append(item)

    candidates.sort(key=lambda x: x.get("published", datetime.min.replace(tzinfo=timezone.utc)), reverse=True)

    if not candidates:
        print("JANTA HOURLY: no new local news in the last 6 hours; nothing posted.")
        return 0

    item = candidates[0]
    title = item["title"]
    source = item.get("source", "Google News")
    link = item["link"]

    output = "janta_ki_awaz_hourly.jpg"
    make_frame(
        headline=title,
        source=source,
        photo_path=None,
        output=output,
    )

    caption = (
        f"📰 {title}\n\n"
        f"स्रोत: {source}\n"
        f"क्षेत्र: अंता | बारां | राजस्थान\n"
        f"समय: {datetime.now(IST).strftime('%d-%m-%Y %H:%M')}\n\n"
        f"#जनताकीआवाज #अंता #बारां #राजस्थान #LocalNews"
    )

    result = post_photo(output, caption)
    print("JANTA HOURLY: Facebook post successful")
    print(result)

    posted.append({
        "link": link,
        "title": normalize_title(title),
        "source": source,
        "posted_at": datetime.now(IST).isoformat(),
    })
    save_posted(posted)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
