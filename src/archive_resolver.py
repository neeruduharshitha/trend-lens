
"""Resolve Google News article links for archive storage."""

from gnews_decoder import decode_many

from src.archive_links import valid_archive_url
from src.publisher_resolver import is_google_news_article_url


def resolve_archive_links(candidates, max_results=30):
    """Resolve supported Google News links to external publishers."""
    if not isinstance(candidates, list):
        return []

    if max_results <= 0:
        return []

    eligible = []
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

        if len(eligible) >= max_results:
            break

    if not eligible:
        return []

    urls = [item["link"] for item in eligible]

    try:
        decoded = decode_many(
            urls,
            concurrency=2,
            timeout=15.0,
        )
    except Exception:
        return []

    if not isinstance(decoded, dict):
        return []

    resolved = []

    for candidate in eligible:
        google_url = candidate["link"]
        publisher_url = decoded.get(google_url)

        if not valid_archive_url(publisher_url):
            continue

        resolved.append({
            **candidate,
            "google_news_url": google_url,
            "publisher_url": publisher_url.strip(),
        })

    return resolved

