import urllib.parse
import urllib.request
import urllib.error
import json
import os
import time

API_VERSION = os.environ.get("INSTAGRAM_API_VERSION", "v26.0")
IG_ID = os.environ.get("VEE_NEWS_INSTAGRAM_ACCOUNT_ID", "").strip()
TOKEN = os.environ.get("VEE_NEWS_INSTAGRAM_ACCESS_TOKEN", "").strip()
MEDIA_URL = os.environ.get("INSTAGRAM_MEDIA_URL", "").strip()
NEWS_TEXT_FILE = os.environ.get("INSTAGRAM_NEWS_TEXT_FILE", "").strip()

if not IG_ID or not TOKEN:
    raise RuntimeError("Instagram account ID or access token secret is missing.")
if not MEDIA_URL:
    raise RuntimeError("INSTAGRAM_MEDIA_URL is missing.")


def api_request(method, path, data=None, params=None):
    url = f"https://graph.instagram.com/{API_VERSION}/{path.lstrip('/')}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    body = None
    headers = {"User-Agent": "VeeNewsInstagramAutomation/1.0"}
    if data is not None:
        body = urllib.parse.urlencode(data).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        print("INSTAGRAM_API_ERROR:", detail)
        raise


def read_caption():
    if NEWS_TEXT_FILE and os.path.isfile(NEWS_TEXT_FILE):
        with open(NEWS_TEXT_FILE, "r", encoding="utf-8") as f:
            text = f.read().strip()
    else:
        candidates = []
        for root in ("incoming_news", "telegram_incoming"):
            if os.path.isdir(root):
                for name in os.listdir(root):
                    if name.lower().endswith((".txt", ".md")):
                        candidates.append(os.path.join(root, name))
        if not candidates:
            raise RuntimeError("No news text file found for Instagram caption.")
        path = max(candidates, key=os.path.getmtime)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().strip()

    text = " ".join(text.split())
    hashtags = "#VeeNews #NewsUpdate #HindiNews #BreakingNews"
    prefix = "Vee News | News Update\n\n"
    available = 2200 - len(prefix) - len(hashtags) - 2
    if available < 1:
        return (prefix + hashtags)[:2200]
    if len(text) > available:
        text = text[:available].rsplit(" ", 1)[0].rstrip(" .,;:।") + "…"
    return prefix + text + "\n\n" + hashtags


def wait_for_media_url(url):
    req = urllib.request.Request(
        url,
        method="HEAD",
        headers={"User-Agent": "VeeNewsInstagramAutomation/1.0"},
    )
    for _ in range(12):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                if 200 <= r.status < 400:
                    print("INSTAGRAM_MEDIA_URL_READY")
                    return
        except Exception as exc:
            print("Waiting for public media URL:", exc)
        time.sleep(3)
    raise RuntimeError("Public GitHub media URL did not become reachable in time.")


def publish_reel():
    caption = read_caption()
    wait_for_media_url(MEDIA_URL)

    print("INSTAGRAM_REEL_CREATE: starting")
    container = api_request(
        "POST",
        f"{IG_ID}/media",
        data={
            "media_type": "REELS",
            "video_url": MEDIA_URL,
            "caption": caption,
            "share_to_feed": "true",
        },
    )

    container_id = container.get("id")
    if not container_id:
        raise RuntimeError(f"Instagram did not return a container id: {container}")
    print("INSTAGRAM_CONTAINER_ID:", container_id)

    for _ in range(30):
        status = api_request(
            "GET",
            container_id,
            params={"fields": "status_code,status"},
        )
        code = status.get("status_code", "")
        print("INSTAGRAM_CONTAINER_STATUS:", code, status.get("status", ""))
        if code == "FINISHED":
            break
        if code in {"ERROR", "EXPIRED"}:
            raise RuntimeError(f"Instagram container failed: {status}")
        time.sleep(5)
    else:
        raise RuntimeError("Instagram container did not finish within the allowed wait time.")

    published = api_request(
        "POST",
        f"{IG_ID}/media_publish",
        data={"creation_id": container_id},
    )
    print("INSTAGRAM_REEL_PUBLISHED:", published)
    return published


if __name__ == "__main__":
    publish_reel()
