import feedparser
import json
import os
import re
import subprocess
import uuid
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher

PAGE_ID = os.environ["FB_PAGE_ID"]
ACCESS_TOKEN = os.environ["FB_PAGE_ACCESS_TOKEN"]
STATE_FILE = "breaking_posted.json"

FEEDS = {
    "India": "https://news.google.com/rss/search?q=India+breaking+news+when:2h&hl=hi&gl=IN&ceid=IN:hi",
    "Rajasthan": "https://news.google.com/rss/search?q=Rajasthan+breaking+news+when:2h&hl=hi&gl=IN&ceid=IN:hi",
    "Kota": "https://news.google.com/rss/search?q=Kota+Rajasthan+breaking+news+when:2h&hl=hi&gl=IN&ceid=IN:hi",
    "National": "https://news.google.com/rss/search?q=India+latest+news+when:2h&hl=hi&gl=IN&ceid=IN:hi",
}

# Words/phrases used only as a signal that a story may be high-impact.
# The script requires both recent publication and an impact signal; it does
# not post every ordinary headline as breaking news.
IMPACT_TERMS = [
    "breaking", "बड़ी खबर", "ताजा खबर", "आपात", "आपातकाल", "भूकंप",
    "बाढ़", "बाढ़", "बारिश", "चक्रवात", "तूफान", "आग", "विस्फोट",
    "दुर्घटना", "हादसा", "मौत", "मारे गए", "गिरफ्तार", "फैसला",
    "आदेश", "चुनाव आयोग", "सरकार ने", "प्रधानमंत्री", "राष्ट्रपति",
    "सुप्रीम कोर्ट", "हाई कोर्ट", "सीमा", "हमला", "युद्ध", "सुरक्षा",
    "earthquake", "flood", "cyclone", "storm", "fire", "explosion",
    "accident", "arrest", "verdict", "court", "election commission",
    "prime minister", "president", "attack", "war", "emergency",
]

JUNK_TERMS = [
    "facebook.com", "#newslive", "#tatagroup", "watch live", "how to watch",
    "कहां और कैसे देखें", "कब, कहां और कैसे देखें", "share market return",
    "6 महीने में", "100% से ज्यादा रिटर्न",
]


def clean(text):
    text = re.sub(r"\s+", " ", str(text)).strip()
    return text


def source_of(entry):
    try:
        source = entry.source.get("title", "") if entry.get("source") else ""
    except Exception:
        source = ""
    if source:
        return clean(source)
    title = clean(entry.get("title", ""))
    if " - " in title:
        return title.rsplit(" - ", 1)[1].strip()
    return "Google News"


def published_time(entry):
    for key in ("published_parsed", "updated_parsed"):
        try:
            value = entry.get(key)
            if value:
                return datetime(*value[:6], tzinfo=timezone.utc)
        except Exception:
            pass
    return None


def normalize(title):
    title = clean(title).lower()
    title = re.sub(r"\s+-\s+[^-]+$", "", title)
    return title


def collect():
    items = []
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=120)

    for category, url in FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                title = clean(entry.get("title", ""))
                link = entry.get("link", "")
                published = published_time(entry)
                source = source_of(entry)
                if not title or not link or not published:
                    continue
                if published < cutoff or published > now + timedelta(minutes=5):
                    continue
                lower = f"{title} {source}".lower()
                if any(term in lower for term in JUNK_TERMS):
                    continue
                if not any(term in lower for term in IMPACT_TERMS):
                    continue
                items.append({
                    "title": title,
                    "link": link,
                    "source": source,
                    "category": category,
                    "published": published,
                })
        except Exception as error:
            print(f"Feed error [{category}]: {error}")

    # Remove exact and near duplicate headlines.
    unique = []
    seen_links = set()
    seen_titles = []
    for item in sorted(items, key=lambda x: x["published"], reverse=True):
        title = normalize(item["title"])
        if item["link"] in seen_links:
            continue
        if any(SequenceMatcher(None, title, old).ratio() >= 0.88 for old in seen_titles):
            continue
        seen_links.add(item["link"])
        seen_titles.append(title)
        unique.append(item)

    print(f"Recent breaking candidates: {len(unique)}")
    for i, item in enumerate(unique[:10], 1):
        age = (now - item["published"]).total_seconds() / 60
        print(f"{i}. {item['title']} [{item['source']}] ({age:.0f} min ago)")
    return unique


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"last_post_time": None, "posted_links": []}


def save_state(state):
    state["posted_links"] = state.get("posted_links", [])[-100:]
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def within_hour(state):
    value = state.get("last_post_time")
    if not value:
        return False
    try:
        last = datetime.fromisoformat(value)
        return datetime.now(timezone.utc) - last < timedelta(hours=1)
    except Exception:
        return False


def main():
    state = load_state()

    if within_hour(state):
        print("Breaking post skipped: last breaking post was less than 1 hour ago.")
        return

    candidates = collect()
    posted_links = set(state.get("posted_links", []))
    candidate = next((item for item in candidates if item["link"] not in posted_links), None)

    if not candidate:
        print("No new high-impact breaking news found.")
        return

    print("\nBREAKING NEWS SELECTED")
    print(candidate["title"])
    print("Source:", candidate["source"])

    image_input = f"{candidate['title']} || {candidate['source']}"
    subprocess.run(["python", "breaking_image_generator.py", image_input], check=True)

    message = """🚨 BREAKING NEWS\n\n#VeenaNews #BreakingNews #HindiNews"""
    photo_url = f"https://graph.facebook.com/v26.0/{PAGE_ID}/photos"
    boundary = uuid.uuid4().hex

    with open("breaking_news_image.jpg", "rb") as image_file:
        image_data = image_file.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="caption"\r\n\r\n'
        f"{message}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="access_token"\r\n\r\n'
        f"{ACCESS_TOKEN}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="source"; filename="breaking_news_image.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8")
    body += image_data
    body += f"\r\n--{boundary}--\r\n".encode("utf-8")

    request = urllib.request.Request(
        photo_url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = response.read().decode("utf-8")
        print("\nFacebook breaking post successful:")
        print(result)
    except urllib.error.HTTPError as e:
        print("\nFacebook breaking post failed:")
        print("HTTP Status:", e.code)
        print(e.read().decode("utf-8", errors="replace"))
        raise

    state["last_post_time"] = datetime.now(timezone.utc).isoformat()
    state.setdefault("posted_links", []).append(candidate["link"])
    save_state(state)
    print("Breaking-news state saved.")


if __name__ == "__main__":
    main()
