
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"


def build_search_query(title, max_terms=5):
    """
    Extract useful title words for Google News search.

    This is a basic keyword search, not semantic matching.
    """

    if not isinstance(title, str):
        return ""

    stop_words = {
        "a", "an", "and", "are", "as", "at", "be",
        "by", "for", "from", "has", "have", "in",
        "into", "is", "it", "its", "of", "on",
        "or", "that", "the", "their", "this",
        "to", "was", "were", "will", "with",
        "new", "latest", "report", "reports",
        "says", "said", "could", "would",
        "should", "after", "before",
    }

    words = re.findall(r"[a-zA-Z0-9]+", title)

    terms = []
    seen = set()

    for word in words:
        normalized = word.lower()

        if len(normalized) < 3:
            continue

        if normalized in stop_words:
            continue

        if normalized in seen:
            continue

        seen.add(normalized)
        terms.append(word)

        if len(terms) >= max_terms:
            break

    return " ".join(terms)


def search_google_news(
    query,
    max_results=30,
    timeout=20,
):
    """
    Search Google News RSS.

    Returns article dictionaries with:
    - title
    - link
    - published
    - source

    Raises RuntimeError on network or parsing failures.
    """

    if not isinstance(query, str) or not query.strip():
        return []

    if max_results <= 0:
        return []

    params = {
        "q": query.strip(),
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en",
    }

    url = (
        GOOGLE_NEWS_RSS_URL
        + "?"
        + urllib.parse.urlencode(params)
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/rss+xml, application/xml",
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)

    except (
        urllib.error.URLError,
        TimeoutError,
        ET.ParseError,
        OSError,
    ) as exc:
        raise RuntimeError(
            f"Google News search failed: {exc}"
        ) from exc

    articles = []
    seen_links = set()

    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        published = (item.findtext("pubDate") or "").strip()

        source_element = item.find("source")
        source = ""

        if source_element is not None:
            source = (
                source_element.text or ""
            ).strip()

        if not title or not link or not published:
            continue

        if link in seen_links:
            continue

        seen_links.add(link)

        articles.append({
            "title": title,
            "link": link,
            "published": published,
            "source": source,
        })

        if len(articles) >= max_results:
            break

    return articles


def search_related_news(
    article_title,
    max_results=30,
):
    """
    Search Google News using keywords from an article title.
    """

    query = build_search_query(article_title)

    if not query:
        return []

    return search_google_news(
        query=query,
        max_results=max_results,
    )
