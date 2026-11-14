
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit, urlunsplit


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be",
    "by", "for", "from", "has", "have", "in",
    "into", "is", "it", "its", "of", "on", "or",
    "that", "the", "their", "this", "to",
    "was", "were", "will", "with", "after",
    "before", "about", "new", "latest",
    "report", "reports", "says", "said",
    "could", "would", "should",
}


def normalize_url(url):
    """Normalize URLs for duplicate detection."""

    if not isinstance(url, str) or not url.strip():
        return ""

    parts = urlsplit(url.strip())

    if parts.scheme.lower() not in ("http", "https"):
        return ""

    if not parts.netloc:
        return ""

    hostname = (parts.hostname or "").lower()

    if not hostname:
        return ""

    # Treat www.example.com and example.com as equivalent.
    if hostname.startswith("www."):
        hostname = hostname[4:]

    if parts.port:
        hostname = f"{hostname}:{parts.port}"

    path = parts.path.rstrip("/") or "/"

    return urlunsplit((
        parts.scheme.lower(),
        hostname,
        path,
        "",
        "",
    ))


def parse_article_date(value):
    """Parse RSS and ISO-style dates into UTC datetimes."""

    if isinstance(value, datetime):
        parsed = value

    elif isinstance(value, str):
        value = value.strip()

        if not value:
            return None

        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError, IndexError):
            try:
                parsed = datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                )
            except ValueError:
                return None

    else:
        return None

    if parsed.tzinfo is None:
        return None

    return parsed.astimezone(timezone.utc)


def tokenize_title(title):
    """Extract meaningful words from an article title."""

    if not isinstance(title, str):
        return set()

    words = re.findall(
        r"[a-z0-9]+",
        title.lower(),
    )

    return {
        word
        for word in words
        if len(word) >= 3 and word not in STOP_WORDS
    }


def relevance_score(current_title, candidate_title):
    """
    Score shared meaningful title terms.

    Returns a value between 0 and 1.
    """

    current_tokens = tokenize_title(current_title)
    candidate_tokens = tokenize_title(candidate_title)

    if not current_tokens or not candidate_tokens:
        return 0.0

    overlap = current_tokens & candidate_tokens

    if not overlap:
        return 0.0

    return len(overlap) / len(current_tokens)


def find_related_history(
    current_article,
    candidates,
    limit=5,
    min_score=0.35,
):
    """
    Find earlier articles with related titles.

    This is candidate discovery, not factual verification.

    Requirements:
    - Both articles have valid dates.
    - Candidate predates the current article.
    - Candidate has a usable HTTP(S) URL.
    - Candidate is not the current article.
    - Duplicate URLs are excluded.
    - Title relevance meets the threshold.

    Returns candidates ordered by relevance,
    then by publication date (newest first).
    """

    if not isinstance(current_article, dict):
        return []

    if not isinstance(candidates, list):
        return []

    if limit <= 0:
        return []

    current_title = current_article.get("title", "")
    current_date = parse_article_date(
        current_article.get("published")
    )
    current_url = normalize_url(
        current_article.get("link")
    )

    if not current_title or current_date is None:
        return []

    results = []
    seen_urls = set()

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue

        title = candidate.get("title", "")
        url = candidate.get("link", "")
        published = candidate.get("published")

        if not isinstance(title, str) or not title.strip():
            continue

        normalized_url = normalize_url(url)

        if not normalized_url:
            continue

        if normalized_url == current_url:
            continue

        candidate_date = parse_article_date(published)

        if candidate_date is None:
            continue

        if candidate_date >= current_date:
            continue

        score = relevance_score(current_title, title)

        if score < min_score:
            continue

        if normalized_url in seen_urls:
            continue

        seen_urls.add(normalized_url)

        results.append({
    "title": title.strip(),
    "link": url,
    "published": published,
    "source": candidate.get("source", ""),
    "published_utc": candidate_date,
    "relevance_score": round(score, 3),
})

    results.sort(
        key=lambda item: (
            item["relevance_score"],
            item["published_utc"],
        ),
        reverse=True,
    )

    return results[:limit]
