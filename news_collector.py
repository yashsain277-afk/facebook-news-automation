import feedparser
import re
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher


# =========================================================
# SETTINGS
# =========================================================

MAX_NEWS_PER_FEED = 5
MAX_CANDIDATES = 20


# =========================================================
# NEWS FEEDS
# =========================================================

FEEDS = {
    "India": (
        "https://news.google.com/rss/search?"
        "q=India&hl=hi&gl=IN&ceid=IN:hi"
    ),

    "Rajasthan": (
        "https://news.google.com/rss/search?"
        "q=Rajasthan&hl=hi&gl=IN&ceid=IN:hi"
    ),

    "Kota": (
        "https://news.google.com/rss/search?"
        "q=Kota+Rajasthan&hl=hi&gl=IN&ceid=IN:hi"
    ),

    "Politics": (
        "https://news.google.com/rss/search?"
        "q=India+Politics&hl=hi&gl=IN&ceid=IN:hi"
    ),

    "Technology": (
        "https://news.google.com/rss/search?"
        "q=Technology+India&hl=hi&gl=IN&ceid=IN:hi"
    ),

    "Business": (
        "https://news.google.com/rss/search?"
        "q=Business+India&hl=hi&gl=IN&ceid=IN:hi"
    ),

    "Sports": (
        "https://news.google.com/rss/search?"
        "q=Sports+India&hl=hi&gl=IN&ceid=IN:hi"
    ),

    "Entertainment": (
        "https://news.google.com/rss/search?"
        "q=Bollywood+India&hl=hi&gl=IN&ceid=IN:hi"
    ),
}


# =========================================================
# TITLE NORMALIZATION
# =========================================================

def normalize_title(title):

    title = str(title)

    # Extra spaces
    title = re.sub(
        r"\s+",
        " ",
        title
    )

    # Google News कभी source को title के अंत में जोड़ता है
    title = re.sub(
        r"\s+-\s+[^-]+$",
        "",
        title
    )

    return title.strip().lower()


# =========================================================
# CLEAN TITLE
# =========================================================

def clean_title(title):

    title = str(title)

    # Extra spaces
    title = re.sub(
        r"\s+",
        " ",
        title
    )

    title = title.strip()

    return title


# =========================================================
# GET SOURCE
# =========================================================

def get_source(entry):

    source = ""

    try:
        if entry.get("source"):
            source = entry.source.get(
                "title",
                ""
            )
    except Exception:
        pass

    if not source:
        title = entry.get(
            "title",
            ""
        )

        # Google News title:
        # Headline - Source
        if " - " in title:

            parts = title.rsplit(
                " - ",
                1
            )

            if len(parts) == 2:
                source = parts[1].strip()

    return source or "Google News"


# =========================================================
# GET PUBLISHED TIME
# =========================================================

def get_published_time(entry):

    try:

        if entry.get("published_parsed"):

            return datetime(
                *entry.published_parsed[:6],
                tzinfo=timezone.utc
            )

    except Exception:
        pass

    try:

        if entry.get("updated_parsed"):

            return datetime(
                *entry.updated_parsed[:6],
                tzinfo=timezone.utc
            )

    except Exception:
        pass

    return datetime.now(
        timezone.utc
    )


# =========================================================
# GET NEWS FROM ONE FEED
# =========================================================

def get_news(
    category,
    feed_url
):

    news_items = []

    try:

        feed = feedparser.parse(
            feed_url
        )

    except Exception as error:

        print(
            f"Feed error [{category}]: "
            f"{error}"
        )

        return news_items


    entries = feed.entries[
        :MAX_NEWS_PER_FEED
    ]


    for entry in entries:

        raw_title = entry.get(
            "title",
            ""
        )

        link = entry.get(
            "link",
            ""
        )

        if not raw_title or not link:
            continue


        title = clean_title(
            raw_title
        )


        # Google News source
        source = get_source(
            entry
        )


        published = get_published_time(
            entry
        )


        news_items.append(
            {
                "title": title,
                "link": link,
                "source": source,
                "category": category,
                "published": published,
            }
        )


    print(
        f"{category}: "
        f"{len(news_items)} news"
    )

    return news_items


# =========================================================
# COLLECT ALL NEWS
# =========================================================

def collect_all_news():

    print(
        "\nCollecting latest news..."
    )

    all_news = []


    for category, feed_url in FEEDS.items():

        news = get_news(
            category,
            feed_url
        )

        all_news.extend(
            news
        )


    print(
        f"\nTotal collected: "
        f"{len(all_news)}"
    )

    return all_news


# =========================================================
# REMOVE DUPLICATES
# =========================================================

def remove_duplicates(
    news_items
):

    unique_news = []

    seen_links = set()
    seen_titles = []


    for item in news_items:

        link = item.get(
            "link",
            ""
        )

        title = normalize_title(
            item.get(
                "title",
                ""
            )
        )


        # Same link
        if link in seen_links:
            continue


        # Same / almost same headline
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


        seen_links.add(
            link
        )

        seen_titles.append(
            title
        )

        unique_news.append(
            item
        )


    print(
        f"After duplicate removal: "
        f"{len(unique_news)}"
    )

    return unique_news


# =========================================================
# SORT BY DATE
# =========================================================

def sort_by_date(
    news_items
):

    return sorted(
        news_items,
        key=lambda item: item.get(
            "published",
            datetime.min.replace(
                tzinfo=timezone.utc
            )
        ),
        reverse=True
    )


# =========================================================
# POST WINDOW
# =========================================================

def get_post_window():

    india_timezone = timezone(
        timedelta(
            hours=5,
            minutes=30
        )
    )

    now = datetime.now(
        india_timezone
    )

    hour = now.hour


    # Morning post
    if 6 <= hour < 14:

        window_name = "MORNING"

        start = now.replace(
            hour=18,
            minute=0,
            second=0,
            microsecond=0
        ) - timedelta(
            days=1
        )


    # Evening post
    elif 14 <= hour <= 23:

        window_name = "EVENING"

        start = now.replace(
            hour=10,
            minute=0,
            second=0,
            microsecond=0
        )


    # Manual testing
    else:

        window_name = "TEST"

        start = now - timedelta(
            hours=12
        )


    print(
        f"\nPost window: "
        f"{window_name}"
    )

    print(
        "Window start:",
        start.strftime(
            "%Y-%m-%d %H:%M"
        )
    )

    print(
        "Window end:",
        now.strftime(
            "%Y-%m-%d %H:%M"
        )
    )

    return (
        start.astimezone(
            timezone.utc
        ),
        now.astimezone(
            timezone.utc
        ),
        window_name
    )


# =========================================================
# SELECT LATEST NEWS
# =========================================================

def select_topics(
    news_items,
    count=20
):

    if not news_items:
        return []


    start_utc, end_utc, window_name = (
        get_post_window()
    )


    # -----------------------------------------------------
    # पहले आज की / current window की news
    # -----------------------------------------------------

    fresh_news = []

    for item in news_items:

        published = item.get(
            "published"
        )

        if not published:
            continue


        if (
            start_utc
            <= published
            <= end_utc
        ):

            fresh_news.append(
                item
            )


    print(
        f"Fresh news in window: "
        f"{len(fresh_news)}"
    )


    # -----------------------------------------------------
    # अगर window में बहुत कम news मिले
    # तो latest news से list पूरी करें
    # -----------------------------------------------------

    if len(fresh_news) < 10:

        print(
            "Fresh news कम है, "
            "latest news से list पूरी की जाएगी."
        )

        fresh_links = {
            item["link"]
            for item in fresh_news
        }


        for item in news_items:

            if item["link"] not in fresh_links:

                fresh_news.append(
                    item
                )

                fresh_links.add(
                    item["link"]
                )


            if len(fresh_news) >= count:
                break


    # -----------------------------------------------------
    # Date के हिसाब से latest first
    # -----------------------------------------------------

    fresh_news = sort_by_date(
        fresh_news
    )


    # -----------------------------------------------------
    # Category diversity
    #
    # एक ही category की सारी headlines
    # लगातार आने से रोकना
    # -----------------------------------------------------

    selected = []

    category_count = {}


    # पहले हर category से limited news
    for item in fresh_news:

        category = item.get(
            "category",
            "Other"
        )

        current_count = category_count.get(
            category,
            0
        )


        if current_count >= 4:
            continue


        selected.append(
            item
        )

        category_count[
            category
        ] = current_count + 1


        if len(selected) >= count:
            break


    # -----------------------------------------------------
    # अगर count पूरा नहीं हुआ
    # remaining latest news जोड़ें
    # -----------------------------------------------------

    if len(selected) < count:

        selected_links = {
            item["link"]
            for item in selected
        }


        for item in fresh_news:

            if item["link"] in selected_links:
                continue


            selected.append(
                item
            )

            selected_links.add(
                item["link"]
            )


            if len(selected) >= count:
                break


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


    return selected[:count]


# =========================================================
# COMPATIBILITY FUNCTION
# =========================================================

def select_topic(
    news_items
):

    topics = select_topics(
        news_items,
        count=1
    )

    if topics:
        return topics[0]

    return None


# =========================================================
# MAIN
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
        count=MAX_CANDIDATES
    )


    print(
        "\n==================================="
    )

    print(
        "LATEST NEWS CANDIDATES"
    )

    print(
        "==================================="
    )


    for index, item in enumerate(
        selected,
        start=1
    ):

        print(
            f"{index}. "
            f"{item['title']}"
        )

        print(
            f"   Source: "
            f"{item['source']}"
        )

        print(
            f"   Category: "
            f"{item['category']}"
        )


    print(
        "\nNews collection completed."
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()
