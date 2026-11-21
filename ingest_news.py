
import argparse
import logging

from src.collector import fetch_all_news
from src.news_storage import init_db, save_articles

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
    args = parser.parse_args()

    articles = fetch_all_news()

    print(f"\nCollected {len(articles)} unique articles.")

    if args.dry_run:
        for article in articles[:15]:
            print(
                f"{article['published']} | "
                f"{article['title']} | "
                f"{article['link']}"
            )
        return

    dated_articles = [
        article for article in articles if article["published"]
    ]

    init_db()
    saved = save_articles(dated_articles)

    print(f"Processed {saved} dated article records.")
    print(
        f"Skipped {len(articles) - len(dated_articles)} "
        "articles without valid publication dates."
    )


if __name__ == "__main__":
    main()
