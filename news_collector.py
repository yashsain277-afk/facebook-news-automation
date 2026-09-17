import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
import re
from difflib import SequenceMatcher


# =========================================================
# GOOGLE NEWS RSS FEEDS
# =========================================================

BASE_URL = "https://news.google.com/rss/search?"

FEEDS = [
    # India
    {
        "name": "India",
        "url": BASE_URL + urllib.parse.urlencode({
            "q": "India",
            "hl": "hi",
            "gl": "IN",
            "ceid": "IN:hi",
        }),
    },

    # Rajasthan
    {
        "name": "Rajasthan",
        "url": BASE_URL + urllib.parse.urlencode({
            "q": "Rajasthan",
            "hl": "hi",
            "gl": "IN",
            "ceid": "IN:hi",
        }),
    },

    # Kota
    {
        "name": "Kota",
        "url": BASE_URL + urllib.parse.urlencode({
            "q": "Kota Rajasthan",
            "hl": "hi",
            "gl": "IN",
            "ceid": "IN:hi",
        }),
    },

    # National politics / government
    {
        "name": "Politics",
        "url": BASE_URL + urllib.parse.urlencode({
            "q": "India politics government",
            "hl": "hi",
            "gl": "IN",
            "ceid": "IN:hi",
        }),
    },

    # Technology
    {
        "name": "Technology",
        "url": BASE_URL + urllib.parse.urlencode({
            "q": "technology India",
            "hl": "hi",
            "gl": "IN",
            "ceid": "IN:hi",
        }),
    },

    # Business
    {
        "name": "Business",
        "url": BASE_URL + urllib.parse.urlencode({
            "q": "India business economy",
            "hl": "hi",
            "gl": "IN",
            "ceid": "IN:hi",
        }),
    },

    # Sports
    {
        "name": "Sports",
        "url": BASE_URL + urllib.parse.urlencode({
            "q": "India sports",
            "hl": "hi",
            "gl": "IN",
            "ceid": "IN:hi",
        }),
    },

    # Entertainment
    {
        "name": "Entertainment",
        "url": BASE_URL + urllib.parse.urlencode({
            "q": "Bollywood entertainment India",
            "hl": "hi",
            "gl": "IN",
            "ceid": "IN:hi",
        }),
    },
]


# =========================================================
# TIMEZONE
# =========================================================

IST = timezone(timedelta(hours=5, minutes=30))


# =========================================================
# TEXT CLEANING
# =========================================================

def clean_text(text):
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text


def normalize_title(title):
    """
    Duplicate detection के लिए headline normalize करता है.
    """

    title = clean_text(title)

    # Google News में कभी-कभी source title के बाद आता है
    title = re.sub(
        r"\s*[-|–—]\s*[^-|–—]+$",
        "",
        title
    )

    title = title.lower()

    # punctuation हटाएं
    title = re.sub(
        r"[^\w\s\u0900-\u097F]",
        " ",
        title
    )

    title = re.sub(
        r"\s+",
        " ",
        title
    )

    return title.strip()


# =========================================================
# DATE PARSER
# =========================================================

def parse_date(date_text):
    """
    RSS pubDate को datetime में बदलता है.
    """

    if not date_text:
        return datetime.now(IST)

    # RSS date formats
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M %z",
        "%d %b %Y %H:%M:%S %z",
        "%d %b %Y %H:%M %z",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(
                date_text,
                fmt
            )

            return dt.astimezone(IST)

        except Exception:
            continue

    return datetime.now(IST)


# =========================================================
# SOURCE EXTRACTION
# =========================================================

def extract_source(title, source_element=None):
    """
    Google News title से source निकालने की कोशिश.
    """

    if source_element is not None:

        source_name = source_element.text

        if source_name:
            return clean_text(source_name)

    # fallback
    separators = [
        " - ",
        " | ",
        " – ",
        " — ",
    ]

    for separator in separators:

        if separator in title:

            parts = title.rsplit(
                separator,
                1
            )

            if len(parts) == 2:

                possible_source = clean_text(
                    parts[1]
                )

                if 2 <= len(possible_source) <= 80:
                    return possible_source

    return "Google News"


# =========================================================
# FETCH RSS
# =========================================================

def fetch_feed(feed):
    """
    एक RSS feed fetch करता है.
    """

    results = []

    try:

        request = urllib.request.Request(
            feed["url"],
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "VeenaNewsBot/1.0"
                )
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            data = response.read()

        root = ET.fromstring(data)

        channel = root.find("channel")

        if channel is None:
            return results

        items = channel.findall("item")

        for item in items[:25]:

            title_element = item.find("title")
            link_element = item.find("link")
            date_element = item.find("pubDate")
            source_element = item.find(
                "{http://search.yahoo.com/mrss/}source"
            )

            if title_element is None:
                continue

            title = clean_text(
                title_element.text or ""
            )

            link = ""

            if link_element is not None:
                link = clean_text(
                    link_element.text or ""
                )

            if not title:
                continue

            published_text = ""

            if date_element is not None:
                published_text = (
                    date_element.text or ""
                )

            published = parse_date(
                published_text
            )

            source = extract_source(
                title,
                source_element
            )

            # Source suffix हटाकर clean headline
            clean_title = title

            if source:
                suffix = (
                    " - " + source
                )

                if clean_title.endswith(
                    suffix
                ):
                    clean_title = clean_title[
                        :-len(suffix)
                    ]

            clean_title = clean_text(
                clean_title
            )

            results.append({
                "title": clean_title,
                "link": link,
                "source": source,
                "published": published,
                "category": feed["name"],
            })

    except Exception as error:

        print(
            f"Feed failed: {feed['name']} "
            f"-> {error}"
        )

    return results


# =========================================================
# COLLECT ALL NEWS
# =========================================================

def collect_all_news():
    """
    सभी RSS feeds से news collect करता है.
    """

    all_news = []

    print("\nCollecting news...\n")

    for feed in FEEDS:

        items = fetch_feed(feed)

        print(
            f"{feed['name']}: "
            f"{len(items)} news"
        )

        all_news.extend(items)

    print(
        f"\nTotal collected: "
        f"{len(all_news)}"
    )

    return all_news


# =========================================================
# DUPLICATE REMOVAL
# =========================================================

def remove_duplicates(news_items):
    """
    Same headline/link को हटाता है.
    """

    unique = []

    seen_links = set()
    seen_titles = []

    for item in news_items:

        link = item.get(
            "link",
            ""
        ).strip()

        title = normalize_title(
            item.get(
                "title",
                ""
            )
        )

        if not title:
            continue

        # Exact link duplicate
        if link and link in seen_links:
            continue

        # Similar title duplicate
        duplicate = False

        for old_title in seen_titles:

            similarity = SequenceMatcher(
                None,
                title,
                old_title
            ).ratio()

            if similarity >= 0.88:
                duplicate = True
                break

        if duplicate:
            continue

        if link:
            seen_links.add(link)

        seen_titles.append(title)

        unique.append(item)

    print(
        f"After duplicate removal: "
        f"{len(unique)}"
    )

    return unique


# =========================================================
# SORT BY DATE
# =========================================================

def sort_by_date(news_items):
    """
    Latest news पहले.
    """

    return sorted(
        news_items,
        key=lambda item: item.get(
            "published",
            datetime.min.replace(
                tzinfo=IST
            )
        ),
        reverse=True
    )


# =========================================================
# POST WINDOW
# =========================================================

def get_post_window():
    """
    Morning / Evening posting window.
    """

    now = datetime.now(IST)

    if 6 <= now.hour < 14:

        start = (
            now.replace(
                hour=6,
                minute=0,
                second=0,
                microsecond=0
            )
            - timedelta(hours=12)
        )

        return start, now, "MORNING"

    elif 14 <= now.hour <= 23:

        start = now.replace(
            hour=10,
            minute=0,
            second=0,
            microsecond=0
        )

        return start, now, "EVENING"

    else:

        start = now - timedelta(
            hours=12
        )

        return start, now, "NIGHT_TEST"


# =========================================================
# HEADLINE SIMILARITY
# =========================================================

def is_similar_to_selected(
    title,
    selected
):
    """
    Selected headlines में बहुत similar headline
    होने से रोकता है.
    """

    normalized = normalize_title(
        title
    )

    for item in selected:

        old = normalize_title(
            item["title"]
        )

        similarity = SequenceMatcher(
            None,
            normalized,
            old
        ).ratio()

        if similarity >= 0.72:
            return True

    return False


# =========================================================
# SELECT TOPICS
# =========================================================

def select_topics(
    news_items,
    count=10
):
    """
    सबसे relevant और अलग-अलग headlines चुनता है.

    पहले recent news,
    फिर category diversity,
    फिर similarity filtering.
    """

    if not news_items:
        return []

    now = datetime.now(IST)

    window_start, window_end, window_name = (
        get_post_window()
    )

    print(
        f"\nPost window: {window_name}"
    )

    print(
        f"Window start: "
        f"{window_start.strftime('%Y-%m-%d %H:%M')}"
    )

    print(
        f"Window end: "
        f"{window_end.strftime('%Y-%m-%d %H:%M')}"
    )

    # -----------------------------------------------------
    # पहले 24 घंटे की fresh news
    # -----------------------------------------------------

    fresh_news = []

    for item in news_items:

        published = item.get(
            "published"
        )

        if not published:
            continue

        if (
            now - timedelta(hours=24)
            <= published
            <= now + timedelta(minutes=10)
        ):
            fresh_news.append(item)

    print(
        f"Fresh news (24h): "
        f"{len(fresh_news)}"
    )

    # अगर fresh news पर्याप्त नहीं है
    # तो सभी available news use करें
    if len(fresh_news) < count:

        fallback = [
            item
            for item in news_items
            if item not in fresh_news
        ]

        candidates = (
            fresh_news + fallback
        )

    else:

        candidates = fresh_news

    # -----------------------------------------------------
    # Score candidates
    # -----------------------------------------------------

    scored = []

    category_bonus = {
        "India": 10,
        "Rajasthan": 12,
        "Kota": 14,
        "Politics": 8,
        "Technology": 7,
        "Business": 7,
        "Sports": 7,
        "Entertainment": 5,
    }

    for item in candidates:

        published = item.get(
            "published",
            now
        )

        age_hours = (
            now - published
        ).total_seconds() / 3600

        # Negative age को zero करें
        age_hours = max(
            0,
            age_hours
        )

        # Recent news को ज्यादा score
        recency_score = max(
            0,
            50 - age_hours * 2
        )

        category = item.get(
            "category",
            ""
        )

        category_score = category_bonus.get(
            category,
            3
        )

        # Window में आने वाली news को bonus
        window_score = 0

        if (
            window_start
            <= published
            <= window_end
        ):
            window_score = 20

        total_score = (
            recency_score
            + category_score
            + window_score
        )

        scored.append(
            (
                total_score,
                item
            )
        )

    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    # -----------------------------------------------------
    # Diverse selection
    # -----------------------------------------------------

    selected = []

    category_counts = {}

    # पहले category diversity
    for score, item in scored:

        if len(selected) >= count:
            break

        category = item.get(
            "category",
            "Other"
        )

        # एक ही category की अधिकतम 3 news
        if category_counts.get(
            category,
            0
        ) >= 3:
            continue

        title = item.get(
            "title",
            ""
        )

        if not title:
            continue

        if is_similar_to_selected(
            title,
            selected
        ):
            continue

        selected.append(item)

        category_counts[category] = (
            category_counts.get(
                category,
                0
            ) + 1
        )

    # -----------------------------------------------------
    # अगर 10 नहीं हुए तो remaining candidates से भरें
    # -----------------------------------------------------

    if len(selected) < count:

        for score, item in scored:

            if len(selected) >= count:
                break

            title = item.get(
                "title",
                ""
            )

            if not title:
                continue

            if any(
                item.get("link")
                == old.get("link")
                for old in selected
            ):
                continue

            if is_similar_to_selected(
                title,
                selected
            ):
                continue

            selected.append(item)

    # -----------------------------------------------------
    # Final sort: latest first
    # -----------------------------------------------------

    selected = sort_by_date(
        selected
    )

    print(
        f"\nSelected headlines: "
        f"{len(selected)}"
    )

    for index, item in enumerate(
        selected,
        start=1
    ):

        print(
            f"{index}. "
            f"{item['title']} "
            f"[{item['category']}]"
        )

    return selected


# =========================================================
# COMPATIBILITY FUNCTION
# =========================================================

def select_topic(news_items):
    """
    पुराने code के लिए compatibility.
    """

    topics = select_topics(
        news_items,
        count=1
    )

    if topics:
        return topics[0]

    return None


# =========================================================
# MAIN TEST
# =========================================================

def main():

    all_news = collect_all_news()

    unique_news = remove_duplicates(
        all_news
    )

    sorted_news = sort_by_date(
        unique_news
    )

    selected = select_topics(
        sorted_news,
        count=10
    )

    print("\n===================================")
    print("       FINAL 10 HEADLINES")
    print("===================================\n")

    for index, item in enumerate(
        selected,
        start=1
    ):

        print(
            f"{index}. {item['title']}"
        )

        print(
            f"   Category: "
            f"{item['category']}"
        )

        print(
            f"   Source: "
            f"{item['source']}"
        )

        print()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()
