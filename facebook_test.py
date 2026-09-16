import os
import urllib.parse
import urllib.request
import subprocess

from news_collector import (
    collect_all_news,
    remove_duplicates,
    sort_by_date,
    select_topic,
)


PAGE_ID = os.environ["FB_PAGE_ID"]
ACCESS_TOKEN = os.environ["FB_PAGE_ACCESS_TOKEN"]


# News collect करें
all_news = collect_all_news()
unique_news = remove_duplicates(all_news)
sorted_news = sort_by_date(unique_news)
selected = select_topic(sorted_news)

if not selected:
    raise RuntimeError("कोई news topic नहीं मिला")


headline = selected["title"]
source = selected["source"]
link = selected["link"]


# News image बनाएं
subprocess.run(
    ["python", "image_generator.py", headline],
    check=True
)


message = f"""📰 आज की बड़ी खबर

{headline}

स्रोत: {source}

पूरी खबर:
{link}

#VeenaNews #News #HindiNews
"""


# पहले image Facebook पर upload करें
photo_url = f"https://graph.facebook.com/v26.0/{PAGE_ID}/photos"

photo_data = urllib.parse.urlencode({
    "caption": message,
    "access_token": ACCESS_TOKEN,
}).encode("utf-8")


with open("news_image.jpg", "rb") as image_file:

    request = urllib.request.Request(
        photo_url,
        data=photo_data,
        method="POST"
    )

    # multipart upload के लिए अलग request बनाएँ
    import http.client
    import uuid

    boundary = uuid.uuid4().hex

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

    body += image_file.read()

    body += f"\r\n--{boundary}--\r\n".encode("utf-8")

    request = urllib.request.Request(
        photo_url,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = response.read().decode("utf-8")

        print("Facebook image post successful:")
        print(result)

    except Exception as e:
        print("Facebook image post failed:")
        print(e)
        raise
