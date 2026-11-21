
import pytest

from src.archive_links import valid_archive_url


@pytest.mark.parametrize(
    "url",
    [
        "https://techcrunch.com/2026/11/example",
        "https://www.reuters.com/technology/example",
        "https://www.nasa.gov/example",
        "https://time.com/article/example",
    ],
)
def test_accepts_public_publisher_links(url):
    assert valid_archive_url(url) is True


@pytest.mark.parametrize(
    "url",
    [
        "",
        None,
        "http://techcrunch.com/example",
        "https://localhost/test",
        "https://news.google.com/rss/articles/example",
        "https://127.0.0.1/test",
        "https://192.168.1.1/test",
        "https://example.local/test",
        "https://user:password@example.com/test",
        "file:///etc/passwd",
    ],
)
def test_rejects_invalid_archive_links(url):
    assert valid_archive_url(url) is False

