
from urllib.parse import urlsplit

from src.history_retriever import (
    parse_article_date,
    relevance_score,
    tokenize_title,
)

from src.history_topics import (
    extract_topics,
    topic_relevance,
)


def is_publisher_url(url):
    """Require an HTTP(S) article URL outside Google News."""

    if not isinstance(url, str):
        return False

    try:
        parsed = urlsplit(url.strip())
        host = (parsed.hostname or "").lower()
        port = parsed.port
    except ValueError:
        return False

    if parsed.scheme not in ("http", "https"):
        return False

    if not host or port is not None:
        return False

    if host == "localhost":
        return False

    if host.endswith((".local", ".internal")):
        return False

    if host in ("news.google.com", "google.com"):
        return False

    if host.endswith(".google.com"):
        return False

    if not "." in host:
        return False

    return True


def clean_article_text(text, max_chars=12000):
    """Normalize extracted article text."""

    if not isinstance(text, str):
        return ""

    cleaned = " ".join(text.split())

    return cleaned[:max_chars]


def get_evidence_excerpt(
    article_text,
    shared_terms,
    max_chars=500,
):
    """
    Find a passage containing overlapping headline terms.

    The excerpt is supporting text for later evaluation,
    not proof that a historical claim is true.
    """

    if not article_text or not shared_terms:
        return ""

    sentences = article_text.replace("!", ".").replace(
        "?", "."
    ).split(".")

    best_sentence = ""
    best_overlap = 0

    for sentence in sentences:
        sentence = sentence.strip()

        if not sentence:
            continue

        sentence_tokens = tokenize_title(sentence)
        overlap = len(sentence_tokens & shared_terms)

        if overlap > best_overlap:
            best_overlap = overlap
            best_sentence = sentence

    if best_overlap < 2:
        return ""

    return best_sentence[:max_chars].strip()


def verify_history_candidate(
    current_article,
    candidate,
    min_score=0.35,
    min_text_chars=150,
):
    """
    Screen a historical candidate for usable evidence.

    Candidate must contain:
      title, published, source, publisher_url, article_text

    Returns an evidence-ready record or None.

    This is automated screening, not independent
    fact-checking or proof of causal relevance.
    """

    if not isinstance(current_article, dict):
        return None

    if not isinstance(candidate, dict):
        return None

    current_title = current_article.get("title", "")
    candidate_title = candidate.get("title", "")

    if not isinstance(current_title, str):
        return None

    if not isinstance(candidate_title, str):
        return None

    current_date = parse_article_date(
        current_article.get("published")
    )

    candidate_date = parse_article_date(
        candidate.get("published")
    )

    if current_date is None or candidate_date is None:
        return None

    if candidate_date >= current_date:
        return None

    publisher_url = candidate.get("publisher_url", "")

    if not is_publisher_url(publisher_url):
        return None

    source = candidate.get("source", "")

    if not isinstance(source, str) or not source.strip():
        return None

    lexical_score = relevance_score(
    current_title,
    candidate_title,
)

    semantic_score = topic_relevance(
        current_title,
        candidate_title,
    )

    score = max(lexical_score, semantic_score)

    if score < min_score:
        return None

    current_tokens = tokenize_title(current_title)
    candidate_tokens = tokenize_title(candidate_title)

    shared_terms = current_tokens & candidate_tokens

    shared_topics = (
    extract_topics(current_title)
    & extract_topics(candidate_title)
)

    if len(shared_terms) < 2 and len(shared_topics) < 2:
        return None

    article_text = clean_article_text(
        candidate.get("article_text", "")
    )

    if len(article_text) < min_text_chars:
        return None

    evidence_terms = set(shared_terms)

    if len(shared_terms) < 2:
        evidence_terms |= tokenize_title(candidate_title)

    evidence = get_evidence_excerpt(
        article_text,
        evidence_terms,
    )

    if not evidence:
        return None

    return {
        "title": candidate_title.strip(),
        "published": candidate.get("published"),
        "published_utc": candidate_date,
        "source": source.strip(),
        "publisher_url": publisher_url.strip(),
        "google_news_url": candidate.get("link", ""),
        "relevance_score": round(score, 3),
        "shared_terms": sorted(shared_terms),
        "evidence_excerpt": evidence,
        "article_text": article_text,
        "status": "evidence_ready",
    }


def verify_history_candidates(
    current_article,
    candidates,
    limit=5,
):
    """Screen and rank a collection of candidates."""

    if not isinstance(candidates, list) or limit <= 0:
        return []

    verified = []
    seen_urls = set()

    for candidate in candidates:
        result = verify_history_candidate(
            current_article,
            candidate,
        )

        if result is None:
            continue

        url = result["publisher_url"]

        if url in seen_urls:
            continue

        seen_urls.add(url)
        verified.append(result)

    verified.sort(
        key=lambda item: (
            item["relevance_score"],
            item["published_utc"],
        ),
        reverse=True,
    )

    return verified[:limit]
