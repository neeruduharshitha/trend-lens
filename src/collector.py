
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import feedparser

logger = logging.getLogger(__name__)

NEWS_SOURCES = {
    "TechCrunch": "https://techcrunch.com/feed/",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "MIT Technology Review": "https://www.technologyreview.com/feed/",
    "Wired": "https://www.wired.com/feed/rss",
    "arXiv AI": "https://export.arxiv.org/rss/cs.AI",
}

TRACKING_PARAMETERS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "source",
}


def canonicalize_url(url):
    """Remove fragments and common tracking parameters from article URLs."""
    if not isinstance(url, str) or not url.strip():
        return ""

    try:
        parts = urlsplit(url.strip())

        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
            return ""

        query = [
            (key, value)
            for key, value in parse_qsl(
                parts.query, keep_blank_values=True
            )
            if not key.lower().startswith("utm_")
            and key.lower() not in TRACKING_PARAMETERS
        ]

        path = parts.path.rstrip("/") or "/"

        return urlunsplit(
            (
                parts.scheme.lower(),
                parts.netloc.lower(),
                path,
                urlencode(query),
                "",
            )
        )
    except ValueError:
        return ""


def normalize_published_date(value):
    """Return an ISO UTC timestamp, or an empty string for invalid dates."""
    if not value:
        return ""

    try:
        parsed = parsedate_to_datetime(str(value))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, IndexError, OverflowError):
        pass

    try:
        parsed = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError):
        return ""


def fetch_news(feed_url):
    """Fetch and normalize articles from one RSS or Atom feed."""
    try:
        feed = feedparser.parse(feed_url)
    except Exception as exc:
        logger.warning("Could not fetch feed %s: %s", feed_url, exc)
        return []

    if getattr(feed, "bozo", False):
        logger.warning(
            "Feed reported a parsing issue: %s",
            feed_url,
        )

    articles = []
    seen_links = set()

    for entry in feed.entries:
        title = str(entry.get("title", "")).strip()
        link = canonicalize_url(entry.get("link", ""))

        if not title or not link or link in seen_links:
            continue

        seen_links.add(link)

        articles.append(
            {
                "title": title,
                "link": link,
                "published": normalize_published_date(
                    entry.get("published")
                    or entry.get("updated")
                    or ""
                ),
                "summary": str(entry.get("summary", "")),
            }
        )

    return articles


def fetch_all_news(sources=None):
    """Fetch articles from all configured sources and deduplicate URLs."""
    sources = NEWS_SOURCES if sources is None else sources

    articles = []
    seen_links = set()

    for source_name, feed_url in sources.items():
        logger.info("Fetching news from %s", source_name)

        try:
            source_articles = fetch_news(feed_url)
        except Exception as exc:
            logger.warning(
                "Skipping %s due to an error: %s",
                source_name,
                exc,
            )
            continue

        for article in source_articles:
            link = article["link"]

            if link in seen_links:
                continue

            seen_links.add(link)
            articles.append(article)

    articles.sort(
        key=lambda article: article.get("published", ""),
        reverse=True,
    )

    return articles
