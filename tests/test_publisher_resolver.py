
import unittest
from unittest.mock import patch

from src.publisher_resolver import (
    is_google_news_article_url,
    resolve_publisher_links,
)


GOOGLE_URL = (
    "https://news.google.com/rss/articles/CBMiExample"
)

PUBLISHER_URL = (
    "https://techcrunch.com/2026/11/example-article/"
)

CANDIDATE = {
    "title": "OpenAI introduces new AI tools",
    "link": GOOGLE_URL,
    "published": "Thu, 12 Nov 2026 15:00:00 GMT",
    "source": "TechCrunch",
}


class TestPublisherResolver(unittest.TestCase):

    def test_valid_google_news_url(self):
        self.assertTrue(
            is_google_news_article_url(GOOGLE_URL)
        )

    def test_rejects_other_domains(self):
        self.assertFalse(
            is_google_news_article_url(
                "https://example.com/article"
            )
        )

    def test_rejects_deceptive_google_domain(self):
        self.assertFalse(
            is_google_news_article_url(
                "https://news.google.com.evil.com/rss/articles/abc"
            )
        )

    @patch("src.publisher_resolver.decode_many")
    def test_successful_resolution(self, mock_decode):
        mock_decode.return_value = {
            GOOGLE_URL: PUBLISHER_URL
        }

        results = resolve_publisher_links(
            [CANDIDATE]
        )

        self.assertEqual(len(results), 1)

        self.assertEqual(
            results[0]["publisher_url"],
            PUBLISHER_URL,
        )

        self.assertEqual(
            results[0]["google_news_url"],
            GOOGLE_URL,
        )

    @patch("src.publisher_resolver.decode_many")
    def test_rejects_unapproved_publisher(self, mock_decode):
        mock_decode.return_value = {
            GOOGLE_URL: "https://unknown.example/story"
        }

        results = resolve_publisher_links(
            [CANDIDATE]
        )

        self.assertEqual(results, [])

    @patch("src.publisher_resolver.decode_many")
    def test_handles_resolution_failure(self, mock_decode):
        mock_decode.side_effect = RuntimeError(
            "Google News temporarily unavailable"
        )

        results = resolve_publisher_links(
            [CANDIDATE]
        )

        self.assertEqual(results, [])

    @patch("src.publisher_resolver.decode_many")
    def test_removes_duplicate_google_urls(self, mock_decode):
        mock_decode.return_value = {
            GOOGLE_URL: PUBLISHER_URL
        }

        results = resolve_publisher_links(
            [CANDIDATE, CANDIDATE]
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(
            len(mock_decode.call_args.args[0]),
            1,
        )


if __name__ == "__main__":
    unittest.main()
