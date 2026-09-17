import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import re


FEEDS = {
    "Google News India": "https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi",
    "Google News Technology": "https://news.google.com/rss/search?q=technology&hl=hi&gl=IN&ceid=IN:hi",
    "Google News India Politics": "https://news.google.com/rss/search?q=india%20politics&hl=hi&gl=IN&ceid=IN:hi",
}


INDIA_TZ = ZoneInfo("Asia/Kolkata")


def normalize_title(title):
    title = title.lower()
    title = re.sub(r"[^\w\s]", " ", title)
    title = re.sub(r"\s+", " ", title)
    return title.strip()


def get_news(feed_name, feed_url, limit=15):

    news_items = []

    try:

        request = urllib.request.Request(
            feed_url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            data = response.read()

        root = ET.fromstring(data)

        items = root.findall(".//item")

        for item in items[:limit]:

            title = item.findtext(
                "title",
                default=""
            ).strip()

            link = item.findtext(
                "link",
                default=""
            ).strip()

            pub_date = item.findtext(
                "pubDate",
                default=""
            ).strip()

            publisher = feed_name

            # Google News title से publisher निकालें
            if " - " in title:

                title_parts = title.rsplit(
                    " - ",
                    1
                )

                possible_title = title_parts[0].strip()
                possible_publisher = title_parts[1].strip()

                if possible_publisher:

                    title = possible_title
                    publisher = possible_publisher

            if not title:
                continue

            published = None

            if pub_date:

                try:

                    published = parsedate_to_datetime(
                        pub_date
                    )

                    if published.tzinfo is None:

                        published = published.replace(
                            tzinfo=timezone.utc
                        )

                except Exception:

                    published = None

            news_items.append({
                "title": title,
                "link": link,
                "source": publisher,
                "published": published,
            })

    except Exception as e:

        print(
            f"ERROR in {feed_name}: {e}"
        )

    return news_items


def collect_all_news():

    all_news = []

    for feed_name, feed_url in FEEDS.items():

        print(
            f"\nCollecting: {feed_name}"
        )

        news = get_news(
            feed_name,
            feed_url
        )

        all_news.extend(news)

        print(
            f"Found: {len(news)} headlines"
        )

    return all_news


def remove_duplicates(news_items):

    unique_news = []
    seen_titles = set()

    for item in news_items:

        normalized = normalize_title(
            item["title"]
        )

        if normalized in seen_titles:
            continue

        seen_titles.add(normalized)

        unique_news.append(item)

    return unique_news


def sort_by_date(news_items):

    return sorted(
        news_items,
        key=lambda item:
        item["published"]
        or datetime.min.replace(
            tzinfo=timezone.utc
        ),
        reverse=True
    )


def get_post_window():

    now = datetime.now(
        INDIA_TZ
    )

    hour = now.hour

    # सुबह की post:
    # पिछली शाम 6 बजे से सुबह 10 बजे तक
    if 6 <= hour < 14:

        start = (
            now - timedelta(
                days=1
            )
        ).replace(
            hour=18,
            minute=0,
            second=0,
            microsecond=0
        )

        end = now

        slot = "MORNING"

    # शाम की post:
    # सुबह 10 बजे से शाम 6 बजे तक
    elif 14 <= hour <= 23:

        start = now.replace(
            hour=10,
            minute=0,
            second=0,
            microsecond=0
        )

        end = now

        slot = "EVENING"

    else:

        # रात में manual test होने पर
        # पिछले 12 घंटे की खबरें
        start = (
            now - timedelta(
                hours=12
            )
        )

        end = now

        slot = "NIGHT_TEST"

    return start, end, slot


def select_topics(
    news_items,
    count=10
):

    if not news_items:
        return []

    start, end, slot = get_post_window()

    print(
        f"\nPost slot: {slot}"
    )

    print(
        f"News window: {start} → {end}"
    )

    scored_news = []

    for item in news_items:

        score = 0

        published = item["published"]

        # समय की window में आने वाली खबर को priority
        if published:

            published_india = published.astimezone(
                INDIA_TZ
            )

            if start <= published_india <= end:

                score += 10

            else:

                # window से बाहर की पुरानी खबर
                # कम priority
                score -= 10

        # दूसरी headlines से similarity
        title_words = {
            word
            for word in normalize_title(
                item["title"]
            ).split()
            if len(word) > 2
        }

        related_count = 0

        for other in news_items:

            if item is other:
                continue

            other_words = {
                word
                for word in normalize_title(
                    other["title"]
                ).split()
                if len(word) > 2
            }

            common_words = (
                title_words
                & other_words
            )

            if (
                len(common_words) >= 2
                and len(common_words)
                / max(
                    1,
                    len(
                        title_words
                        | other_words
                    )
                ) >= 0.25
            ):

                related_count += 1

        # एक ही विषय कई headlines में हो
        # तो उसे थोड़ा priority
        score += related_count * 3

        # नई खबर को priority
        if published:

            age_hours = (
                datetime.now(
                    timezone.utc
                ) - published
            ).total_seconds() / 3600

            if age_hours <= 6:

                score += 5

            elif age_hours <= 12:

                score += 3

            elif age_hours <= 24:

                score += 1

        scored_news.append(
            (
                score,
                item
            )
        )

    scored_news.sort(
        key=lambda x: x[0],
        reverse=True
    )

    selected = []

    used_titles = set()

    for score, item in scored_news:

        normalized = normalize_title(
            item["title"]
        )

        if normalized in used_titles:
            continue

        used_titles.add(
            normalized
        )

        selected.append(item)

        if len(selected) >= count:
            break

    print(
        f"\nSelected headlines: {len(selected)}"
    )

    for index, item in enumerate(
        selected,
        start=1
    ):

        print(
            f"{index}. {item['title']}"
        )

    return selected


# पुराना code compatibility के लिए
def select_topic(news_items):

    topics = select_topics(
        news_items,
        count=1
    )

    if topics:

        return topics[0]

    return None


def main():

    print(
        "\n==================================="
    )

    print(
        "       VEENA NEWS COLLECTOR"
    )

    print(
        "==================================="
    )

    all_news = collect_all_news()

    print(
        f"\nTotal headlines collected: "
        f"{len(all_news)}"
    )

    unique_news = remove_duplicates(
        all_news
    )

    print(
        f"After duplicate removal: "
        f"{len(unique_news)}"
    )

    sorted_news = sort_by_date(
        unique_news
    )

    selected = select_topics(
        sorted_news,
        count=10
    )

    print(
        "\n==================================="
    )

    print(
        "        SELECTED HEADLINES"
    )

    print(
        "==================================="
    )

    for index, item in enumerate(
        selected,
        start=1
    ):

        print(
            f"\n{index}. {item['title']}"
        )

        print(
            f"Source: {item['source']}"
        )

        print(
            f"Link: {item['link']}"
        )

    print(
        "\n==================================="
    )


if __name__ == "__main__":
    main()
