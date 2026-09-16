import os
import json
import urllib.request
import subprocess
import uuid


from news_collector import (
    collect_all_news,
    remove_duplicates,
    sort_by_date,
    select_topic,
)


PAGE_ID = os.environ["FB_PAGE_ID"]
ACCESS_TOKEN = os.environ["FB_PAGE_ACCESS_TOKEN"]

POSTED_FILE = "posted_news.json"


# पहले पोस्ट की गई खबरें पढ़ें
try:
    with open(POSTED_FILE, "r", encoding="utf-8") as file:
        posted_news = json.load(file)
except Exception:
    posted_news = []


# News collect करें
all_news = collect_all_news()
unique_news = remove_duplicates(all_news)
sorted_news = sort_by_date(unique_news)


# पहले से पोस्ट की गई खबरों को छोड़कर नई खबर चुनें
selected = None

for item in sorted_news:

    normalized_title = normalize_title(item["title"])

    already_posted = False

    for posted in posted_news:

        if posted.get("link") == item["link"]:
            already_posted = True
            break

        if posted.get("title") == normalized_title:
            already_posted = True
            break

    if not already_posted:
        selected = item
        break

if not selected:
    raise RuntimeError("कोई नई news नहीं मिली")


headline = selected["title"]
source = selected["source"]
link = selected["link"]


print("\nSelected NEW NEWS:")
print(headline)
print(link)


# News image बनाएं
subprocess.run(
    ["python", "image_generator.py", headline],
    check=True
)


message = f"""📰 आज की बड़ी खबर

{headline}

यह खबर अभी चर्चा में है। पूरी जानकारी के लिए नीचे दिए गए स्रोत पर जाएँ।

स्रोत: {source}

🔗 पूरी खबर:
{link}

#VeenaNews #News #HindiNews
"""


# Facebook photo upload URL
photo_url = f"https://graph.facebook.com/v26.0/{PAGE_ID}/photos"


# Image को multipart form में तैयार करें
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
    headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}"
    },
    method="POST"
)


# Facebook पर post करें
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


# Successful post के बाद खबर को save करें
posted_news.append(link)

with open(POSTED_FILE, "w", encoding="utf-8") as file:
    json.dump(
        posted_news,
        file,
        ensure_ascii=False,
        indent=2
    )


print("\nNews saved to posted_news.json")
print("Duplicate protection completed.")
