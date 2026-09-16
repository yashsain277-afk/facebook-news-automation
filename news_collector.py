import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import re


FEEDS = {
    "Google News India": "https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi",
    "Google News Technology": "https://news.google.com/rss/search?q=technology&hl=hi&gl=IN&ceid=IN:hi",
    "Google News India Politics": "https://news.google.com/rss/search?q=india%20politics&hl=hi&gl=IN&ceid=IN:hi",
}


def normalize_title(title):
    """Title को comparison के लिए साफ करता है."""
    title = title.lower()
    title = re.sub(r"[^\w\s]", " ", title)
    title = re.sub(r"\s+", " ", title)
    return title.strip()


def get_news(feed_name, feed_url, limit=10):
    """एक RSS feed से news collect करता है."""
    news_items = []

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

        for item in items[:limit]:
            title = item.findtext("title", default="").strip()
            link = item.findtext("link", default="").strip()
            pub_date = item.findtext("pubDate", default="").strip()

            if not title:
                continue

            published = None

            if pub_date:
                try:
                    published = parsedate_to_datetime(pub_date)

                    if published.tzinfo is None:
                        published = published.replace(tzinfo=timezone.utc)

                except Exception:
                    published = None

            news_items.append({
                "title": title,
                "link": link,
                "source": feed_name,
                "published": published,
            })

    except Exception as e:
        print(f"ERROR in {feed_name}: {e}")

    return news_items


def collect_all_news():
    """सभी feeds से news collect करता है."""
    all_news = []

    for feed_name, feed_url in FEEDS.items():
        print(f"\nCollecting: {feed_name}")

        news = get_news(feed_name, feed_url)
        all_news.extend(news)

        print(f"Found: {len(news)} headlines")

    return all_news


def remove_duplicates(news_items):
    """Duplicate headlines हटाता है."""
    unique_news = []
    seen_titles = set()

    for item in news_items:
        normalized = normalize_title(item["title"])

        if normalized in seen_titles:
            continue

        seen_titles.add(normalized)
        unique_news.append(item)

    return unique_news


def sort_by_date(news_items):
    """नई news को पहले रखता है."""
    return sorted(
        news_items,
        key=lambda item: item["published"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True
    )


def select_topic(news_items):
    """अलग wording वाली related news को पहचानकर priority देता है."""

    if not news_items:
        return None

    # बहुत सामान्य शब्द हटाए जाएंगे
    stop_words = {
        "के", "का", "की", "को", "से", "में", "और", "पर",
        "एक", "है", "हैं", "ने", "यह", "इस", "उस",
        "लिए", "बारे", "बाद", "अब", "भी", "तो",
        "the", "a", "an", "and", "of", "in", "to",
        "is", "on", "for"
    }

    scored_news = []

    for item in news_items:
        title_words = {
            word
            for word in normalize_title(item["title"]).split()
            if word not in stop_words and len(word) > 2
        }

        score = 0
        related_count = 0

        for other in news_items:
            if item is other:
                continue

            other_words = {
                word
                for word in normalize_title(other["title"]).split()
                if word not in stop_words and len(word) > 2
            }

            if not title_words or not other_words:
                continue

            common_words = title_words & other_words

            # Jaccard similarity
            similarity = len(common_words) / len(
                title_words | other_words
            )

            # अगर headlines काफी related हैं
            if similarity >= 0.25 and len(common_words) >= 2:
                related_count += 1

        # दूसरी related headlines मिलने पर priority
        score += related_count * 3

        # बहुत recent news को extra priority
        if item["published"]:
            age_hours = (
                datetime.now(timezone.utc) - item["published"]
            ).total_seconds() / 3600

            if age_hours <= 6:
                score += 2
            elif age_hours <= 12:
                score += 1

        scored_news.append((score, item, related_count))

    # सबसे ज्यादा score वाली news पहले
    scored_news.sort(
        key=lambda x: x[0],
        reverse=True
    )

    selected_score, selected, related_count = scored_news[0]

    print(f"\nSelected topic score: {selected_score}")
    print(f"Related headlines found: {related_count}")

    return selected

def main():
    print("\n===================================")
    print("       NEWS TOPIC SELECTOR")
    print("===================================")

    # 1. सभी feeds से news
    all_news = collect_all_news()

    print(f"\nTotal headlines collected: {len(all_news)}")

    # 2. Duplicate हटाना
    unique_news = remove_duplicates(all_news)

    print(f"After duplicate removal: {len(unique_news)}")

    # 3. Date के हिसाब से sort
    sorted_news = sort_by_date(unique_news)

    # 4. Topic select
    selected = select_topic(sorted_news)

    if not selected:
        print("\nNo topic selected.")
        return

    print("\n===================================")
    print("        SELECTED TOPIC")
    print("===================================")

    print(f"\nHeadline: {selected['title']}")
    print(f"Source: {selected['source']}")
    print(f"Link: {selected['link']}")

    if selected["published"]:
        print(f"Published: {selected['published']}")

    print("\n===================================")
    print("Topic selection completed.")
    print("===================================")


if __name__ == "__main__":
    main()
