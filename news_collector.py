import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime


FEEDS = {
    "Google News India": "https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi",
}


def get_news(feed_name, feed_url, limit=10):
    print(f"\n===== {feed_name} =====")

    try:
        request = urllib.request.Request(
            feed_url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            data = response.read()

        root = ET.fromstring(data)

        items = root.findall(".//item")

        if not items:
            print("No news items found.")
            return

        for i, item in enumerate(items[:limit], start=1):
            title = item.findtext("title", default="").strip()
            link = item.findtext("link", default="").strip()
            pub_date = item.findtext("pubDate", default="").strip()

            print(f"\n{i}. {title}")
            print(f"   Link: {link}")

            if pub_date:
                try:
                    dt = parsedate_to_datetime(pub_date)
                    print(f"   Date: {dt}")
                except Exception:
                    print(f"   Date: {pub_date}")

    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    for feed_name, feed_url in FEEDS.items():
        get_news(feed_name, feed_url)
