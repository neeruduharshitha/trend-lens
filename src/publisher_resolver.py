
from urllib.parse import urlsplit

from gnews_decoder import decode_many

from src.publisher_extractor import publisher_host


def is_google_news_article_url(url):
    """
    Return True only for supported Google News
    article URL formats.
    """

    if not isinstance(url, str):
        return False

    try:
        parsed = urlsplit(url.strip())
    except ValueError:
        return False

    if parsed.scheme != "https":
        return False

    if parsed.hostname != "news.google.com":
        return False

    if parsed.username or parsed.password:
        return False

    try:
        if parsed.port not in (None, 443):
            return False
    except ValueError:
        return False

    valid_prefixes = (
        "/rss/articles/",
        "/articles/",
        "/read/",
    )

    return any(
        parsed.path.startswith(prefix)
        and len(parsed.path) > len(prefix)
        for prefix in valid_prefixes
    )


def resolve_publisher_links(candidates, max_results=10):
    """
    Resolve Google News RSS links to publisher URLs.

    Only accept URLs from approved publisher domains.

    Keep original Google News links for traceability.

    Return candidates with a valid publisher_url.
    """

    if not isinstance(candidates, list):
        return []

    if max_results <= 0:
        return []

    eligible = []
    google_urls = []
    seen = set()

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue

        google_url = candidate.get("link", "")

        if not is_google_news_article_url(google_url):
            continue

        if google_url in seen:
            continue

        seen.add(google_url)
        eligible.append(candidate)
        google_urls.append(google_url)

        if len(eligible) >= max_results:
            break

    if not google_urls:
        return []

    try:
        decoded = decode_many(
            google_urls,
            concurrency=2,
            timeout=15.0,
        )
    except Exception:
        # A resolver outage should not crash Trend Lens.
        return []

    if not isinstance(decoded, dict):
        return []

    resolved = []

    for candidate in eligible:
        google_url = candidate["link"]
        publisher_url = decoded.get(google_url)

        if not isinstance(publisher_url, str):
            continue

        publisher_url = publisher_url.strip()

        if not publisher_host(publisher_url):
            continue

        resolved.append({
            **candidate,
            "google_news_url": google_url,
            "publisher_url": publisher_url,
        })

    return resolved
