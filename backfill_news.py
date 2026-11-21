
"""Backfill missing Trend Lens archive dates from Google News RSS."""

import argparse
import logging
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from src.news_search import search_google_news
from src.news_storage import get_articles_for_day, save_articles
from src.archive_resolver import resolve_archive_links


logger = logging.getLogger(__name__)

# Searches are intentionally broad but technology-focused.
SEARCH_TOPICS = (
    "artificial intelligence technology",
    "AI startups funding",
    "technology cybersecurity",
    "semiconductors computing",
)

MAX_SEARCH_RESULTS = 40
MAX_RESOLVE_RESULTS = 30


def parse_published(value):
    """Convert an RSS timestamp to an aware UTC datetime."""
    if not value:
        return None

    try:
        parsed = parsedate_to_datetime(str(value))
    except (TypeError, ValueError, IndexError, OverflowError):
        return None

    if parsed.tzinfo is None:
        return None

    return parsed.astimezone(timezone.utc)


def build_daily_query(topic, day):
    """Restrict a Google News query to one calendar day."""
    next_day = day + timedelta(days=1)

    return (
        f"{topic} "
        f"after:{day.isoformat()} "
        f"before:{next_day.isoformat()}"
    )


def select_daily_candidates(candidates, day):
    """Keep only articles with a timestamp on the target UTC day."""
    selected = []
    seen = set()

    for article in candidates:
        if not isinstance(article, dict):
            continue

        published_at = parse_published(article.get("published"))
        link = str(article.get("link") or "").strip()

        if published_at is None or published_at.date() != day:
            continue

        if not link or link in seen:
            continue

        seen.add(link)
        selected.append(article)

    return selected


def backfill_day(day, dry_run=True):
    """Find and optionally save articles for one UTC calendar date."""
    print(f"\n--- {day.isoformat()} ---")

    discovered = []
    search_errors = 0

    for topic in SEARCH_TOPICS:
        query = build_daily_query(topic, day)

        try:
            results = search_google_news(
                query,
                max_results=MAX_SEARCH_RESULTS,
            )
        except RuntimeError as exc:
            search_errors += 1
            logger.warning("Search failed for %s: %s", query, exc)
            continue

        print(f"Search: {topic} -> {len(results)} results")
        discovered.extend(results)

    candidates = select_daily_candidates(discovered, day)

    print(f"Matching dated articles: {len(candidates)}")

    if not candidates:
        if search_errors:
            print("Some searches failed; results may be incomplete.")
        return 0

    resolved =resolve_archive_links(
        candidates,
        max_results=MAX_RESOLVE_RESULTS,
    )

    print(f"Resolved publisher links: {len(resolved)}")

    prepared = []
    seen_publishers = set()

    for article in resolved:
        publisher_url = article.get("publisher_url")

        if not publisher_url or publisher_url in seen_publishers:
            continue

        seen_publishers.add(publisher_url)

        prepared.append({
            "title": article["title"],
            "link": publisher_url,
            "published": article["published"],
            "summary": "",
        })

    for article in prepared[:5]:
        print(f"  - {article['title']}")
        print(f"    {article['link']}")

    if dry_run:
        print(f"DRY RUN: {len(prepared)} articles ready to save")
        return len(prepared)

    save_articles(prepared)

    stored = get_articles_for_day(day)
    print(f"Articles currently stored for this day: {len(stored)}")

    return len(prepared)


def main():
    parser = argparse.ArgumentParser(
        description="Backfill the Trend Lens news archive."
    )

    parser.add_argument(
        "--start",
        required=True,
        help="First date, YYYY-MM-DD",
    )

    parser.add_argument(
        "--end",
        required=True,
        help="Last date, YYYY-MM-DD",
    )

    parser.add_argument(
        "--save",
        action="store_true",
        help="Write results to SQLite (default is dry run)",
    )

    args = parser.parse_args()

    try:
        start = date.fromisoformat(args.start)
        end = date.fromisoformat(args.end)
    except ValueError:
        parser.error("Dates must use YYYY-MM-DD")

    if end < start:
        parser.error("--end must be on or after --start")

    if (end - start).days > 6:
        parser.error("Backfill at most seven days per run")

    if end > datetime.now(timezone.utc).date():
        parser.error("Cannot backfill future dates")

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s",
    )

    total = 0
    day = start

    while day <= end:
        total += backfill_day(
            day,
            dry_run=not args.save,
        )
        day += timedelta(days=1)

    print("\nBackfill complete.")
    print(f"Articles processed: {total}")

    if not args.save:
        print("No database changes were made.")


if __name__ == "__main__":
    main()
