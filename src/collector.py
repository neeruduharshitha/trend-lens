import feedparser


def fetch_news(feed_url):
    """Fetch, validate, and normalize articles from an RSS feed."""
    feed = feedparser.parse(feed_url)
    articles = []
    seen_links = set()

    for entry in feed.entries:
        if not entry.get("title") or not entry.get("link"):
            continue

        if entry["link"] in seen_links:
            continue

        seen_links.add(entry["link"])

        article = {
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
            "summary": entry.get("summary", ""),
        }
        articles.append(article)

    return articles