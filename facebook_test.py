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

POSTED_FILE = "posted_news.json"


# पहले पोस्ट की गई खबरें पढ़ें
try:

    with open(
        POSTED_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        posted_news = json.load(file)

except Exception:

    posted_news = []


# News collect करें
all_news = collect_all_news()

unique_news = remove_duplicates(
    all_news
)

sorted_news = sort_by_date(
    unique_news
)


# 10 headlines चुनें
candidate_news = select_topics(
    sorted_news,
    count=15
)


# पहले से पोस्ट की गई खबरें हटाएँ
selected_news = []

for item in candidate_news:

    normalized_title = normalize_title(
        item["title"]
    )

    already_posted = False

    for posted in posted_news:

        # पुराने records string/link हैं
        if isinstance(posted, str):

            if posted == item["link"]:

                already_posted = True
                break

        # भविष्य में dictionary records हों
        elif isinstance(posted, dict):

            if posted.get("link") == item["link"]:

                already_posted = True
                break

            if posted.get("title") == normalized_title:

                already_posted = True
                break

    if not already_posted:

        selected_news.append(item)

    if len(selected_news) >= 10:

        break


if not selected_news:

    raise RuntimeError(
        "कोई नई news नहीं मिली"
    )


print("\n===================================")
print("       SELECTED 10 HEADLINES")
print("===================================")


for index, item in enumerate(
    selected_news,
    start=1
):

    print(
        f"{index}. {item['title']}"
    )

    print(
        f"   Source: {item['source']}"
    )


# Image के लिए 10 headlines तैयार करें
image_headlines = "\n".join(
    [
        item["title"]
        for item in selected_news
    ]
)


# News image बनाएं
subprocess.run(
    [
        "python",
        "image_generator.py",
        image_headlines
    ],
    check=True
)


# Facebook caption
caption_lines = [
    "📰 आज की बड़ी खबरें",
    ""
]


for index, item in enumerate(
    selected_news,
    start=1
):

    caption_lines.append(
        f"{index}. {item['title']}"
    )

    caption_lines.append(
        f"स्रोत: {item['source']}"
    )

    caption_lines.append("")


caption_lines.append(
    "#VeenaNews #News #HindiNews"
)


message = "\n".join(
    caption_lines
)


# Facebook photo upload URL
photo_url = (
    f"https://graph.facebook.com/v26.0/"
    f"{PAGE_ID}/photos"
)


# Multipart form
boundary = uuid.uuid4().hex


with open(
    "news_image.jpg",
    "rb"
) as image_file:

    image_data = image_file.read()


body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; '
    f'name="caption"\r\n\r\n'
    f"{message}\r\n"
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; '
    f'name="access_token"\r\n\r\n'
    f"{ACCESS_TOKEN}\r\n"
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; '
    f'name="source"; '
    f'filename="news_image.jpg"\r\n'
    f"Content-Type: image/jpeg\r\n\r\n"
).encode("utf-8")


body += image_data

body += (
    f"\r\n--{boundary}--\r\n"
).encode("utf-8")


request = urllib.request.Request(
    photo_url,
    data=body,
    headers={
        "Content-Type":
        f"multipart/form-data; "
        f"boundary={boundary}"
    },
    method="POST"
)


# Facebook पर post करें
try:

    with urllib.request.urlopen(
        request,
        timeout=60
    ) as response:

        result = response.read().decode(
            "utf-8"
        )

    print(
        "\nFacebook image post successful:"
    )

    print(result)


except urllib.error.HTTPError as e:

    print(
        "\nFacebook image post failed:"
    )

    print(
        "HTTP Status:",
        e.code
    )

    error_body = e.read().decode(
        "utf-8",
        errors="replace"
    )

    print(
        "Facebook error response:"
    )

    print(error_body)

    raise


except Exception as e:

    print(
        "\nFacebook image post failed:"
    )

    print(e)

    raise


# Successful post के बाद
# सभी 10 खबरें save करें
for item in selected_news:

    if item["link"] not in posted_news:

        posted_news.append(
            item["link"]
        )


with open(
    POSTED_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        posted_news,
        file,
        ensure_ascii=False,
        indent=2
    )


print(
    "\n10 news links saved."
)

print(
    "Duplicate protection completed."
)
