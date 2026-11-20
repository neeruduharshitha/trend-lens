
import logging
import re
from datetime import timedelta

from src.history_topics import topic_relevance
from src.historical_queries import (
    generate_historical_queries,
    historical_topic_score,
)
from src.history_retriever import (
    find_related_history,
    parse_article_date,
    tokenize_title,
)
from src.history_verifier import verify_history_candidates
from src.news_search import search_related_news
from src.publisher_extractor import (
    extract_publisher_article,
    publisher_host,
)
from src.publisher_resolver import resolve_publisher_links


logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# 1. Diagnostic logging
# ---------------------------------------------------------

def log_history_stage(stage, candidates):
    """Log the number of candidates remaining at each stage."""
    count = len(candidates) if isinstance(candidates, list) else 0

    logger.info(
        "Trend Lens history | stage=%s | count=%d",
        stage,
        count,
    )


# ---------------------------------------------------------
# 2. Historical query helpers
# ---------------------------------------------------------

EVENT_WORDS = {
    "announce",
    "announced",
    "announces",
    "announcement",
    "launch",
    "launched",
    "launches",
    "launching",
    "introduce",
    "introduced",
    "introduces",
    "unveil",
    "unveiled",
    "unveils",
    "today",
    "yesterday",
    "now",
    "first",
}


def build_historical_query(title, max_terms=5):
    """
    Build a simplified search query from a news headline.

    Retained for compatibility with existing tests
    and other modules.
    """
    if not isinstance(title, str):
        return ""

    if max_terms <= 0:
        return ""

    stop_words = {
        "the", "and", "for", "with", "from",
        "that", "this", "into", "about",
        "after", "before", "their", "will",
        "would", "could", "should", "have",
        "has", "was", "were", "are", "its",
        "new", "latest", "report", "reports",
        "says", "said",
    }

    terms = []
    seen = set()

    for word in re.findall(r"[A-Za-z0-9]+", title):
        normalized = word.lower()

        if len(normalized) < 3:
            continue

        if normalized in stop_words:
            continue

        if normalized in EVENT_WORDS:
            continue

        if normalized in seen:
            continue

        seen.add(normalized)
        terms.append(word)

        if len(terms) >= max_terms:
            break

    return " ".join(terms)


# ---------------------------------------------------------
# 3. Historical date validation
# ---------------------------------------------------------

def sufficiently_historical(
    current_article,
    candidate,
    min_age_days=7,
):
    """
    Require a candidate article to have been published
    before the current article by at least min_age_days.
    """
    if not isinstance(current_article, dict):
        return False

    if not isinstance(candidate, dict):
        return False

    if min_age_days < 0:
        return False

    current_date = parse_article_date(
        current_article.get("published")
    )

    candidate_date = parse_article_date(
        candidate.get("published")
    )

    if current_date is None or candidate_date is None:
        return False

    if candidate_date >= current_date:
        return False

    return (
        current_date - candidate_date
        >= timedelta(days=min_age_days)
    )


# ---------------------------------------------------------
# 4. Duplicate headline detection
# ---------------------------------------------------------

def title_similarity(title_a, title_b):
    """
    Calculate Jaccard similarity between two headlines.

    Used to identify likely duplicate news coverage.
    """
    tokens_a = tokenize_title(title_a)
    tokens_b = tokenize_title(title_b)

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b

    return len(intersection) / len(union)


def diversify_history(candidates, limit=30):
    """
    Reduce near-duplicate headlines.

    Preserve input order, which should already
    reflect historical topic relevance.
    """
    if not isinstance(candidates, list):
        return []

    if limit <= 0:
        return []

    selected = []

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue

        title = candidate.get("title", "")

        if not isinstance(title, str) or not title.strip():
            continue

        duplicate = any(
            title_similarity(
                title,
                existing["title"],
            ) >= 0.65
            for existing in selected
        )

        if duplicate:
            continue

        selected.append(candidate)

        if len(selected) >= limit:
            break

    return selected


# ---------------------------------------------------------
# 5. Publisher article extraction and verification
# ---------------------------------------------------------

def prepare_history_candidates(
    current_article,
    candidates,
    limit=5,
):
    """
    Extract publisher article text and verify
    preliminary historical evidence.
    """
    if not isinstance(candidates, list):
        return []

    if limit <= 0:
        return []

    enriched = []

    skipped_invalid_url = 0
    failed_extraction = 0

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue

        publisher_url = candidate.get(
            "publisher_url",
            "",
        )

        if not publisher_host(publisher_url):
            skipped_invalid_url += 1
            continue

        try:
            article_text = extract_publisher_article(
                publisher_url
            )
        except Exception:
            failed_extraction += 1

            logger.warning(
                "Historical publisher extraction failed: %s",
                publisher_url,
                exc_info=True,
            )
            continue

        if not article_text:
            failed_extraction += 1
            continue

        enriched.append({
            **candidate,
            "article_text": article_text,
        })

    log_history_stage(
        "publisher_text_extracted",
        enriched,
    )

    logger.info(
        "Trend Lens history | invalid_urls=%d | "
        "failed_extractions=%d",
        skipped_invalid_url,
        failed_extraction,
    )

    verified = verify_history_candidates(
        current_article,
        enriched,
        limit=limit,
    )

    log_history_stage(
        "verified_evidence",
        verified,
    )

    return verified


# ---------------------------------------------------------
# 6. Complete historical evidence pipeline
# ---------------------------------------------------------

def build_historical_evidence(
    current_article,
    max_search_results=30,
    max_resolve_results=30,
    limit=5,
    min_age_days=7,
):
    """
    Build source-backed historical evidence.

    Workflow:
    1. Generate multiple historical search queries.
    2. Search Google News.
    3. Deduplicate search results.
    4. Enforce historical publication dates.
    5. Rank candidates by broader topic relevance.
    6. Reduce near-duplicate headlines.
    7. Resolve original publisher URLs.
    8. Extract publisher article text.
    9. Verify preliminary historical evidence.

    Returns evidence-ready candidate records.

    Important:
    These records are not yet verified historical
    timeline milestones.
    """

    # -----------------------------------------------------
    # Validate inputs
    # -----------------------------------------------------

    if not isinstance(current_article, dict):
        logger.warning(
            "Historical pipeline received invalid article."
        )
        return []

    if (
        limit <= 0
        or max_search_results <= 0
        or max_resolve_results <= 0
        or min_age_days < 0
    ):
        logger.warning(
            "Historical pipeline received invalid limits."
        )
        return []

    title = current_article.get("title", "")

    if not isinstance(title, str) or not title.strip():
        logger.warning(
            "Historical pipeline received empty title."
        )
        return []

    current_date = parse_article_date(
        current_article.get("published")
    )

    if current_date is None:
        logger.warning(
            "Historical pipeline could not parse date: %s",
            title,
        )
        return []

    logger.info(
        "Trend Lens history | starting article=%s",
        title,
    )

    # -----------------------------------------------------
    # Generate historical search queries
    # -----------------------------------------------------

    generated_queries = generate_historical_queries(
        title,
        max_queries=4,
    )

    queries = [title]
    seen_queries = {title.strip().lower()}

    for query in generated_queries:
        if not isinstance(query, str):
            continue

        normalized = query.strip().lower()

        if not normalized:
            continue

        if normalized in seen_queries:
            continue

        seen_queries.add(normalized)
        queries.append(query)

    logger.info(
        "Trend Lens history | search_queries=%s",
        queries,
    )

    # -----------------------------------------------------
    # Search Google News
    # -----------------------------------------------------

    all_candidates = []
    seen_links = set()

    for query in queries:
        try:
            found = search_related_news(
                query,
                max_results=max_search_results,
            )

        except RuntimeError:
            logger.warning(
                "Historical news search failed: %s",
                query,
                exc_info=True,
            )
            continue

        if not isinstance(found, list):
            logger.warning(
                "Historical search returned invalid data "
                "for query: %s",
                query,
            )
            continue

        logger.info(
            "Trend Lens history | query=%s | results=%d",
            query,
            len(found),
        )

        for candidate in found:
            if not isinstance(candidate, dict):
                continue

            link = candidate.get("link", "")

            if not isinstance(link, str) or not link:
                continue

            if link in seen_links:
                continue

            seen_links.add(link)
            all_candidates.append(candidate)

    log_history_stage(
        "search",
        all_candidates,
    )

    if not all_candidates:
        logger.info(
            "Historical pipeline stopped: no search results."
        )
        return []

    # -----------------------------------------------------
    # Filter historical publication dates
    # -----------------------------------------------------

    historical = [
        candidate
        for candidate in all_candidates
        if sufficiently_historical(
            current_article,
            candidate,
            min_age_days=min_age_days,
        )
    ]

    log_history_stage(
        "historical_dates",
        historical,
    )

    if not historical:
        logger.info(
            "Historical pipeline stopped: "
            "no sufficiently old articles."
        )
        return []

    # -----------------------------------------------------
    # Validate URLs and rank historical candidates
    # -----------------------------------------------------

    # Title overlap threshold is zero here because
    # broader topic relevance is evaluated next.

    related = find_related_history(
        current_article,
        historical,
        limit=len(historical),
        min_score=0.0,
    )

    log_history_stage(
        "valid_related_urls",
        related,
    )

    if not related:
        logger.info(
            "Historical pipeline stopped: "
            "no valid related article URLs."
        )
        return []

    # Calculate historical topic relevance.
    for candidate in related:
        candidate["historical_topic_score"] = max(
            historical_topic_score(
                title,
                candidate["title"],
            ),
            topic_relevance(
                title,
                candidate["title"],
            ),
        )

    # Remove candidates with little topic connection.
    related = [
        candidate
        for candidate in related
        if candidate["historical_topic_score"] >= 0.15
    ]

    log_history_stage(
        "topic_relevance",
        related,
    )

    if not related:
        logger.info(
            "Historical pipeline stopped: "
            "no sufficiently relevant articles."
        )
        return []

    # Rank stronger topic matches first.
    related.sort(
        key=lambda article: (
            article["historical_topic_score"],
            article["published_utc"],
        ),
        reverse=True,
    )

    # -----------------------------------------------------
    # Reduce duplicate historical coverage
    # -----------------------------------------------------

    diverse = diversify_history(
        related,
        limit=max_resolve_results,
    )

    log_history_stage(
        "diversified",
        diverse,
    )

    if not diverse:
        logger.info(
            "Historical pipeline stopped: "
            "no diverse historical articles."
        )
        return []

    # -----------------------------------------------------
    # Resolve original publisher URLs
    # -----------------------------------------------------

    resolved = resolve_publisher_links(
        diverse,
        max_results=max_resolve_results,
    )

    log_history_stage(
        "publisher_resolution",
        resolved,
    )

    if not resolved:
        logger.info(
            "Historical pipeline stopped: "
            "publisher links could not be resolved."
        )
        return []

    # -----------------------------------------------------
    # Extract and verify publisher evidence
    # -----------------------------------------------------

    verified = prepare_history_candidates(
        current_article,
        resolved,
        limit=limit,
    )

    logger.info(
        "Trend Lens history | completed | "
        "verified_candidates=%d",
        len(verified),
    )

    return verified
