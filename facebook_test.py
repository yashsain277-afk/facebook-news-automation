import os
import urllib.parse
import urllib.request

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

# Duplicate हटाएँ
unique_news = remove_duplicates(all_news)

# नई news पहले
sorted_news = sort_by_date(unique_news)

# Trending/important topic चुनें
selected = select_topic(sorted_news)

if not selected:
    raise RuntimeError("कोई news topic नहीं मिला")


headline = selected["title"]
source = selected["source"]
link = selected["link"]


message = f"""📰 आज की बड़ी खबर

{headline}

स्रोत: {source}

पूरी खबर:
{link}

#VeenaNews #News #HindiNews
"""


url = f"https://graph.facebook.com/v26.0/{PAGE_ID}/feed"

data = urllib.parse.urlencode({
    "message": message,
    "access_token": ACCESS_TOKEN,
}).encode("utf-8")


request = urllib.request.Request(
    url,
    data=data,
    method="POST"
)


try:
    with urllib.request.urlopen(request, timeout=30) as response:
        result = response.read().decode("utf-8")

    print("Facebook post successful:")
    print(result)

except Exception as e:
    print("Facebook post failed:")
    print(e)
