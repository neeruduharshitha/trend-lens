
import sqlite3
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit

DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "trend_lens.db"


def _published_at(value):
    """Normalize RSS or ISO publication dates to UTC."""
    if not value:
        return None

    try:
        parsed = parsedate_to_datetime(str(value))
    except (TypeError, ValueError, IndexError, OverflowError):
        try:
            parsed = datetime.fromisoformat(
                str(value).replace("Z", "+00:00")
            )
        except (TypeError, ValueError, OverflowError):
            return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc).isoformat()


def _connect(db_path):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path=DEFAULT_DB_PATH):
    """Create the news database if it doesn't exist."""
    with _connect(db_path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                link TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                summary TEXT NOT NULL DEFAULT '',
                published TEXT NOT NULL DEFAULT '',
                published_at TEXT,
                collected_at TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_published_at
            ON articles(published_at)
        """)


def save_articles(articles, db_path=DEFAULT_DB_PATH):
    """Insert or update articles without creating duplicates."""
    init_db(db_path)
    saved = 0

    with _connect(db_path) as connection:
        for article in articles:
            if not isinstance(article, dict):
                continue

            title = str(article.get("title") or "").strip()
            link = str(article.get("link") or "").strip()

            parsed_url = urlsplit(link)
            if (
                not title
                or parsed_url.scheme not in ("http", "https")
                or not parsed_url.netloc
            ):
                continue

            published = str(article.get("published") or "")
            published_at = _published_at(published)
            summary = str(article.get("summary") or "")

            before = connection.total_changes

            connection.execute("""
                INSERT INTO articles (
                    link, title, summary, published,
                    published_at, collected_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(link) DO UPDATE SET
                    title = excluded.title,
                    summary = CASE
                        WHEN excluded.summary != ''
                        THEN excluded.summary
                        ELSE articles.summary
                    END,
                    published = CASE
                        WHEN excluded.published_at IS NOT NULL
                        THEN excluded.published
                        ELSE articles.published
                    END,
                    published_at = COALESCE(
                        excluded.published_at,
                        articles.published_at
                    )
            """, (
                link,
                title,
                summary,
                published,
                published_at,
                datetime.now(timezone.utc).isoformat(),
            ))

            saved += connection.total_changes - before

    return saved


def get_articles_for_day(day, db_path=DEFAULT_DB_PATH):
    """Return articles published on a given UTC calendar date."""
    if isinstance(day, datetime):
        day = day.date()

    if isinstance(day, date):
        day = day.isoformat()
    else:
        day = date.fromisoformat(str(day)).isoformat()

    init_db(db_path)

    with _connect(db_path) as connection:
        rows = connection.execute("""
            SELECT title, link, summary, published
            FROM articles
            WHERE substr(published_at, 1, 10) = ?
            ORDER BY published_at DESC, link ASC
        """, (day,)).fetchall()

    return [dict(row) for row in rows]
