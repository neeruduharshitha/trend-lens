
import sqlite3
from pathlib import Path

from src.supabase_storage import (
    get_client,
    save_articles_supabase,
)

DB_PATH = Path("data/trend_lens.db")


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"SQLite database not found: {DB_PATH}")

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        articles = [
            dict(row)
            for row in connection.execute(
                """
                SELECT title, link, summary, published
                FROM articles
                ORDER BY published_at DESC
                """
            ).fetchall()
        ]
    finally:
        connection.close()

    print(f"Found {len(articles)} articles in SQLite.")

    if not articles:
        print("Nothing to migrate.")
        return

    client = get_client()
    processed = save_articles_supabase(articles, client=client)

    result = (
        client.table("articles")
        .select("link", count="exact")
        .limit(1)
        .execute()
    )

    print(f"Processed {processed} articles.")
    print(f"Total articles in Supabase: {result.count}")


if __name__ == "__main__":
    main()
