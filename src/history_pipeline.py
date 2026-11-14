
from src.history_verifier import verify_history_candidates

from src.publisher_extractor import (
    extract_publisher_article,
    publisher_host,
)


def prepare_history_candidates(
    current_article,
    candidates,
    limit=5,
):
    """
    Enrich historical news candidates with publisher
    article text and screen them for usable evidence.

    Parameters:
        current_article: The currently selected news article.

        candidates: List of potentially related
                    historical articles.

        limit: Maximum number of results to return.

    Returns:
        List of evidence-ready historical candidates.
    """

    if not isinstance(candidates, list):
        return []

    if limit <= 0:
        return []

    enriched = []

    for candidate in candidates:

        if not isinstance(candidate, dict):
            continue

        # Get the original publisher URL
        publisher_url = candidate.get(
            "publisher_url",
            "",
        )

        # Skip missing or unsupported publisher URLs
        if not publisher_host(publisher_url):
            continue

        # Extract article text
        article_text = extract_publisher_article(
            publisher_url
        )

        # Skip articles that cannot be extracted
        if not article_text:
            continue

        # Preserve original metadata and add article text
        enriched.append({
            **candidate,
            "article_text": article_text,
        })

    # Apply historical evidence screening
    return verify_history_candidates(
        current_article,
        enriched,
        limit=limit,
    )
