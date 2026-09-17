# पहले से पोस्ट की गई खबरों को छोड़कर नई खबर चुनें
selected = None

for item in sorted_news:

    normalized_title = normalize_title(item["title"])

    already_posted = False

    for posted in posted_news:

        # पुराने records string/link के रूप में हैं
        if isinstance(posted, str):
            if posted == item["link"]:
                already_posted = True
                break

        # नए records dictionary के रूप में हो सकते हैं
        elif isinstance(posted, dict):

            if posted.get("link") == item["link"]:
                already_posted = True
                break

            if posted.get("title") == normalized_title:
                already_posted = True
                break

    if not already_posted:
        selected = item
        break
