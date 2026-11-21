
from types import SimpleNamespace

from src import collector


def test_canonicalize_url_removes_tracking():
    url = (
        "https://example.com/story/?utm_source=rss"
        "&id=123#section"
    )

    assert collector.canonicalize_url(url) == (
        "https://example.com/story?id=123"
    )


def test_invalid_url_is_rejected():
    assert collector.canonicalize_url("javascript:alert(1)") == ""
    assert collector.canonicalize_url("") == ""


def test_normalize_rfc2822_date():
    result = collector.normalize_published_date(
        "Fri, 20 Nov 2026 10:00:00 GMT"
    )

    assert result == "2026-11-20T10:00:00+00:00"


def test_invalid_date_returns_empty_string():
    assert collector.normalize_published_date("not a date") == ""


def test_fetch_news_deduplicates(monkeypatch):
    fake_feed = SimpleNamespace(
        bozo=False,
        entries=[
            {
                "title": "AI story",
                "link": "https://example.com/ai?utm_source=rss",
                "published": "Fri, 20 Nov 2026 10:00:00 GMT",
                "summary": "First article",
            },
            {
                "title": "AI story",
                "link": "https://example.com/ai",
                "published": "Fri, 20 Nov 2026 10:00:00 GMT",
            },
            {
                "title": "",
                "link": "https://example.com/empty",
            },
        ],
    )

    monkeypatch.setattr(
        collector.feedparser,
        "parse",
        lambda url: fake_feed,
    )

    articles = collector.fetch_news("https://example.com/rss")

    assert len(articles) == 1
    assert articles[0]["title"] == "AI story"


def test_fetch_all_news_deduplicates_across_sources(monkeypatch):
    def fake_fetch(url):
        if url == "feed-a":
            return [
                {
                    "title": "First",
                    "link": "https://example.com/first",
                    "published": "2026-11-20T10:00:00+00:00",
                    "summary": "",
                }
            ]

        return [
            {
                "title": "Duplicate",
                "link": "https://example.com/first",
                "published": "2026-11-20T10:00:00+00:00",
                "summary": "",
            },
            {
                "title": "Second",
                "link": "https://example.com/second",
                "published": "2026-11-21T10:00:00+00:00",
                "summary": "",
            },
        ]

    monkeypatch.setattr(collector, "fetch_news", fake_fetch)

    articles = collector.fetch_all_news(
        {"Source A": "feed-a", "Source B": "feed-b"}
    )

    assert len(articles) == 2
    assert articles[0]["title"] == "Second"


def test_broken_feed_does_not_stop_collection(monkeypatch):
    def fake_fetch(url):
        if url == "broken":
            raise RuntimeError("Network failure")

        return [
            {
                "title": "Working article",
                "link": "https://example.com/working",
                "published": "2026-11-21T10:00:00+00:00",
                "summary": "",
            }
        ]

    monkeypatch.setattr(collector, "fetch_news", fake_fetch)

    articles = collector.fetch_all_news(
        {"Broken": "broken", "Working": "working"}
    )

    assert len(articles) == 1
    assert articles[0]["title"] == "Working article"
