
import argparse
import logging

from src.collector import fetch_all_news
from src.news_storage import init_db, save_articles
from src.supabase_storage import save_articles_supabase

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)


def main():
    parser = argparse.ArgumentParser(
        description="Collect and store Trend Lens RSS articles."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview articles without saving them.",
    )
    parser.add_argument(
        "--sqlite",
        action="store_true",
        help="Save to local SQLite instead of Supabase.",
    )
    args = parser.parse_args()

    articles = fetch_all_news()
    print(f"\nCollected {len(articles)} unique articles.")

    if args.dry_run:
        for article in articles[:15]:
            print(
                f"{article.get('published', '')} | "
                f"{article.get('title', '')} | "
                f"{article.get('link', '')}"
            )
        return

    dated_articles = [
        article
        for article in articles
        if article.get("published")
    ]

    if not dated_articles:
        logging.warning("No dated articles collected; nothing to save.")
        return

    if args.sqlite:
        init_db()
        processed = save_articles(dated_articles)
        destination = "SQLite"
    else:
        processed = save_articles_supabase(dated_articles)
        destination = "Supabase"

    print(f"Processed {processed} dated article records in {destination}.")
    print(
        f"Skipped {len(articles) - len(dated_articles)} "
        "articles without publication dates."
    )


if __name__ == "__main__":
    main()
