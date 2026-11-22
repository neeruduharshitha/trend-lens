
import os
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlsplit

from dotenv import load_dotenv
from supabase import create_client

from src.news_storage import _published_at

load_dotenv()


def get_client():
    """Create a backend-only Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY")

    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SECRET_KEY "
            "must be configured."
        )

    return create_client(url, key)


def save_articles_supabase(articles, client=None):
    """Save articles while preserving existing summaries and dates."""
    client = client if client is not None else get_client()
    processed = 0

    for article in articles:
        if not isinstance(article, dict):
            continue

        title = str(article.get("title") or "").strip()
        link = str(article.get("link") or "").strip()

        try:
            parts = urlsplit(link)
            valid_link = (
                parts.scheme in ("http", "https")
                and bool(parts.hostname)
            )
        except ValueError:
            valid_link = False

        if not title or not valid_link:
            continue

        published = str(article.get("published") or "")
        published_at = _published_at(published)
        summary = str(article.get("summary") or "")

        existing_response = (
            client.table("articles")
            .select("summary,published,published_at")
            .eq("link", link)
            .limit(1)
            .execute()
        )

        existing = (
            existing_response.data[0]
            if existing_response.data
            else {}
        )

        record = {
            "link": link,
            "title": title,
            "summary": summary or existing.get("summary") or "",
            "published": (
                published
                if published_at
                else existing.get("published") or published
            ),
            "published_at": (
                published_at or existing.get("published_at")
            ),
        }

        client.table("articles").upsert(
            record,
            on_conflict="link",
        ).execute()

        processed += 1

    return processed


def get_articles_for_day_supabase(day, client=None):
    """Retrieve articles for one UTC calendar date."""
    client = client if client is not None else get_client()

    if isinstance(day, datetime):
        day = day.astimezone(timezone.utc).date()
    elif not isinstance(day, date):
        day = date.fromisoformat(str(day))

    start = datetime(
        day.year, day.month, day.day,
        tzinfo=timezone.utc,
    )
    end = start + timedelta(days=1)

    response = (
        client.table("articles")
        .select("title,link,summary,published")
        .gte("published_at", start.isoformat())
        .lt("published_at", end.isoformat())
        .order("published_at", desc=True)
        .order("link")
        .limit(1000)
        .execute()
    )

    return response.data or []
