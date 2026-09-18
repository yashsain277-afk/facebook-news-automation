import os
import json
import subprocess
import uuid
import urllib.request
import urllib.error

from news_collector import (
    collect_all_news,
    remove_duplicates,
    sort_by_date,
    select_topics,
    normalize_title,
)

PAGE_ID = os.environ["FB_PAGE_ID"]
ACCESS_TOKEN = os.environ["FB_PAGE_ACCESS_TOKEN"]
POSTED_FILE = os.environ.get("POSTED_FILE", "posted_news.json")
PAGE_NAME = os.environ.get("PAGE_NAME", "Veena News")
LOCATION_LINE = os.environ.get("LOCATION_LINE", "📍 अंता | बारां | राजस्थान")
HASHTAGS = os.environ.get(
    "HASHTAGS",
    "#VeenaNews #Anta #Baran #RajasthanNews #LocalNews #HindiNews",
)

try:
    with open(POSTED_FILE, "r", encoding="utf-8") as file:
        posted_news = json.load(file)
except Exception:
    posted_news = []

recent_posted_news = posted_news[-10:]

all_news = collect_all_news()
unique_news = remove_duplicates(all_news)

filtered_news = []
for item in unique_news:
    source = str(item.get("source", "")).strip().lower()
    title = str(item.get("title", "")).strip().lower()

    if "facebook.com" in source or "facebook.com" in title:
        print(f"Skipping Facebook source: {item.get('title', '')}")
        continue

    if "#newslive" in title or "#tatagroup" in title:
        print(f"Skipping social-media style headline: {item.get('title', '')}")
        continue

    filtered_news.append(item)

sorted_news = sort_by_date(filtered_news)
window_news = select_topics(sorted_news, count=20)

selected_news = []
selected_links = set()

for item in window_news:
    normalized_title = normalize_title(item["title"])
    already_posted = False

    for posted in recent_posted_news:
        if isinstance(posted, str) and posted == item["link"]:
            already_posted = True
            break
        if isinstance(posted, dict):
            if posted.get("link") == item["link"]:
                already_posted = True
                break
            if posted.get("title") == normalized_title:
                already_posted = True
                break

    if not already_posted:
        selected_news.append(item)
        selected_links.add(item["link"])

    if len(selected_news) >= 10:
        break

if len(selected_news) < 10:
    for item in sorted_news:
        if item["link"] in selected_links:
            continue
        selected_news.append(item)
        selected_links.add(item["link"])
        print(f"Filling headline slot from latest available news: {item['title']}")
        if len(selected_news) >= 10:
            break

if not selected_news:
    print("\nकोई usable news उपलब्ध नहीं है — आज post नहीं किया जाएगा।")
    raise SystemExit(0)

selected_news = selected_news[:10]

print("\n===================================")
print(f"       SELECTED {len(selected_news)} HEADLINES")
print("===================================")

for index, item in enumerate(selected_news, start=1):
    print(f"{index}. {item['title']}")
    print(f"   Source: {item['source']}")

image_items = [f"{item['title']} || {item['source']}" for item in selected_news]
image_input = "\n".join(image_items)

subprocess.run(["python", "image_generator.py", image_input], check=True)

caption_lines = [f"📰 {PAGE_NAME} - आज की 10 बड़ी स्थानीय खबरें", ""]
for index, item in enumerate(selected_news, start=1):
    caption_lines.append(f"{index}. {item['title']}")
    caption_lines.append(f"   स्रोत: {item['source']}")
    if index != len(selected_news):
        caption_lines.append("")

caption_lines.extend(["", LOCATION_LINE, "", HASHTAGS])
message = "\n".join(caption_lines)

photo_url = f"https://graph.facebook.com/v26.0/{PAGE_ID}/photos"
boundary = uuid.uuid4().hex

with open("news_image.jpg", "rb") as image_file:
    image_data = image_file.read()

body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="caption"\r\n\r\n'
    f"{message}\r\n"
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="access_token"\r\n\r\n'
    f"{ACCESS_TOKEN}\r\n"
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="source"; filename="news_image.jpg"\r\n'
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
    print("\nFacebook image post successful:")
    print(result)
except urllib.error.HTTPError as e:
    print("\nFacebook image post failed:")
    print("HTTP Status:", e.code)
    error_body = e.read().decode("utf-8", errors="replace")
    print("Facebook error response:")
    print(error_body)
    raise
except Exception as e:
    print("\nFacebook image post failed:")
    print(e)
    raise

for item in selected_news:
    if item["link"] not in posted_news:
        posted_news.append(item["link"])

posted_news = posted_news[-100:]

with open(POSTED_FILE, "w", encoding="utf-8") as file:
    json.dump(posted_news, file, ensure_ascii=False, indent=2)

print("\n10 news links saved.")
print("Recent duplicate protection completed.")
