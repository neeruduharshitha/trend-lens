
import unittest
from unittest.mock import patch

from src.publisher_extractor import (
    publisher_host,
    has_public_dns,
    extract_publisher_article,
)
from src.history_pipeline import (
    prepare_history_candidates,
)


CURRENT = {
    "title": "OpenAI announces new AI agent platform",
    "published": "Fri, 13 Nov 2026 20:00:00 GMT",
}

CANDIDATE = {
    "title": "OpenAI introduces AI agent tools",
    "published": "Thu, 12 Nov 2026 15:00:00 GMT",
    "link": "https://news.google.com/rss/articles/example",
    "publisher_url": "https://techcrunch.com/example",
    "source": "TechCrunch",
}

ARTICLE_TEXT = (
    "OpenAI introduced AI agent tools for developers. "
    "The tools allowed developers to build applications "
    "that performed multi-step tasks. "
    "The announcement described several platform "
    "features for software developers. "
    "These capabilities were part of an earlier "
    "generation of agent development tools."
)


class TestPublisherExtractor(unittest.TestCase):

    def test_accepts_approved_publisher(self):
        self.assertEqual(
            publisher_host(
                "https://techcrunch.com/example"
            ),
            "techcrunch.com",
        )

    def test_rejects_google_news(self):
        self.assertIsNone(
            publisher_host(
                "https://news.google.com/rss/articles/abc"
            )
        )

    def test_rejects_localhost(self):
        self.assertIsNone(
            publisher_host(
                "http://localhost:8000/article"
            )
        )

    def test_rejects_unapproved_domain(self):
        self.assertIsNone(
            publisher_host(
                "https://unknown.example/article"
            )
        )

    def test_rejects_deceptive_domain(self):
        self.assertIsNone(
            publisher_host(
                "https://techcrunch.com.evil.example/story"
            )
        )

    def test_rejects_non_https(self):
        self.assertIsNone(
            publisher_host(
                "http://techcrunch.com/story"
            )
        )

    @patch("src.publisher_extractor.socket.getaddrinfo")
    def test_rejects_private_dns(self, mock_dns):
        mock_dns.return_value = [
            (2, 1, 6, "", ("127.0.0.1", 443))
        ]

        self.assertFalse(
            has_public_dns("techcrunch.com")
        )

    @patch("src.publisher_extractor.has_public_dns")
    def test_rejects_failed_dns(self, mock_dns):
        mock_dns.return_value = False

        result = extract_publisher_article(
            "https://techcrunch.com/example"
        )

        self.assertIsNone(result)

    @patch("src.history_pipeline.extract_publisher_article")
    def test_pipeline_with_article_text(self, mock_extract):
        mock_extract.return_value = ARTICLE_TEXT

        result = prepare_history_candidates(
            CURRENT,
            [CANDIDATE],
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(
            result[0]["status"],
            "evidence_ready",
        )

    @patch("src.history_pipeline.extract_publisher_article")
    def test_pipeline_skips_failed_extraction(self, mock_extract):
        mock_extract.return_value = None

        result = prepare_history_candidates(
            CURRENT,
            [CANDIDATE],
        )

        self.assertEqual(result, [])

    @patch("src.history_pipeline.extract_publisher_article")
    def test_pipeline_skips_google_news_link(self, mock_extract):
        candidate = {
            **CANDIDATE,
            "publisher_url": CANDIDATE["link"],
        }

        result = prepare_history_candidates(
            CURRENT,
            [candidate],
        )

        self.assertEqual(result, [])
        mock_extract.assert_not_called()


if __name__ == "__main__":
    unittest.main()
