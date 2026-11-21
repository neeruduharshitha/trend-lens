
from datetime import date

from src.news_storage import (
    get_articles_for_day,
    init_db,
    save_articles,
)


def test_database_initialization(tmp_path):
    db_path = tmp_path / "news.db"

    init_db(db_path)

    assert db_path.exists()


def test_save_and_retrieve_article(tmp_path):
    db_path = tmp_path / "news.db"

    article = {
        "title": "New AI model announced",
        "link": "https://example.com/ai-model",
        "summary": "An AI research announcement.",
        "published": "Wed, 18 Nov 2026 10:00:00 GMT",
    }

    save_articles([article], db_path)

    results = get_articles_for_day(
        date(2026, 11, 18),
        db_path,
    )

    assert len(results) == 1
    assert results[0] == article


def test_duplicate_articles_are_not_repeated(tmp_path):
    db_path = tmp_path / "news.db"

    article = {
        "title": "AI research update",
        "link": "https://example.com/research",
        "summary": "Research news.",
        "published": "Wed, 18 Nov 2026 09:00:00 GMT",
    }

    save_articles([article], db_path)
    save_articles([article], db_path)

    results = get_articles_for_day(
        "2026-11-18",
        db_path,
    )

    assert len(results) == 1


def test_articles_are_filtered_by_publication_date(tmp_path):
    db_path = tmp_path / "news.db"

    articles = [
        {
            "title": "Wednesday news",
            "link": "https://example.com/wednesday",
            "summary": "",
            "published": "Wed, 18 Nov 2026 12:00:00 GMT",
        },
        {
            "title": "Tuesday news",
            "link": "https://example.com/tuesday",
            "summary": "",
            "published": "Tue, 17 Nov 2026 12:00:00 GMT",
        },
    ]

    save_articles(articles, db_path)

    results = get_articles_for_day(
        "2026-11-17",
        db_path,
    )

    assert len(results) == 1
    assert results[0]["title"] == "Tuesday news"


def test_invalid_articles_are_skipped(tmp_path):
    db_path = tmp_path / "news.db"

    save_articles([
        {"title": "", "link": "https://example.com/empty"},
        {"title": "Missing URL", "link": ""},
        {"title": "Unsafe URL", "link": "javascript:alert(1)"},
    ], db_path)

    assert get_articles_for_day(
        "2026-11-18",
        db_path,
    ) == []


def test_timezone_conversion_uses_utc_date(tmp_path):
    db_path = tmp_path / "news.db"

    article = {
        "title": "Late evening announcement",
        "link": "https://example.com/late",
        "summary": "",
        "published": "Tue, 17 Nov 2026 23:30:00 -0500",
    }

    save_articles([article], db_path)

    assert len(get_articles_for_day(
        "2026-11-18", db_path
    )) == 1


def test_articles_survive_database_reopening(tmp_path):
    db_path = tmp_path / "news.db"

    save_articles([{
        "title": "Stored news",
        "link": "https://example.com/stored",
        "summary": "",
        "published": "Wed, 18 Nov 2026 08:00:00 GMT",
    }], db_path)

    # A separate call opens a new database connection.
    results = get_articles_for_day(
        "2026-11-18",
        db_path,
    )

    assert len(results) == 1
