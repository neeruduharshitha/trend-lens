
import unittest

from src.history_verifier import (
    clean_article_text,
    get_evidence_excerpt,
    is_publisher_url,
    verify_history_candidate,
    verify_history_candidates,
)


CURRENT = {
    "title": "OpenAI announces new AI agent platform",
    "link": "https://example.com/current",
    "published": "Fri, 13 Nov 2026 20:00:00 GMT",
}

ARTICLE_TEXT = (
    "OpenAI introduced AI agent tools for developers "
    "earlier this year. "
    "The tools helped developers build applications "
    "that could perform multi-step tasks. "
    "The announcement described software development "
    "features and early platform capabilities. "
    "Developers were able to experiment with agent "
    "workflows using the available tools."
)

CANDIDATE = {
    "title": "OpenAI introduces AI agent tools",
    "link": "https://news.google.com/rss/articles/example",
    "publisher_url": "https://example.com/earlier-story",
    "published": "Thu, 12 Nov 2026 15:00:00 GMT",
    "source": "Example News",
    "article_text": ARTICLE_TEXT,
}


class TestHistoryVerifier(unittest.TestCase):

    def test_valid_candidate(self):
        result = verify_history_candidate(
            CURRENT,
            CANDIDATE,
        )

        self.assertIsNotNone(result)
        self.assertEqual(
            result["status"],
            "evidence_ready",
        )

    def test_rejects_google_news_url(self):
        candidate = {
            **CANDIDATE,
            "publisher_url": (
                "https://news.google.com/rss/articles/abc"
            ),
        }

        self.assertIsNone(
            verify_history_candidate(CURRENT, candidate)
        )

    def test_rejects_missing_publisher_url(self):
        candidate = {
            **CANDIDATE,
            "publisher_url": "",
        }

        self.assertIsNone(
            verify_history_candidate(CURRENT, candidate)
        )

    def test_rejects_future_article(self):
        candidate = {
            **CANDIDATE,
            "published": "Sat, 14 Nov 2026 15:00:00 GMT",
        }

        self.assertIsNone(
            verify_history_candidate(CURRENT, candidate)
        )

    def test_rejects_unrelated_article(self):
        candidate = {
            **CANDIDATE,
            "title": "Scientists discover ocean species",
        }

        self.assertIsNone(
            verify_history_candidate(CURRENT, candidate)
        )

    def test_rejects_short_article_text(self):
        candidate = {
            **CANDIDATE,
            "article_text": "OpenAI agent tools.",
        }

        self.assertIsNone(
            verify_history_candidate(CURRENT, candidate)
        )

    def test_rejects_missing_source(self):
        candidate = {
            **CANDIDATE,
            "source": "",
        }

        self.assertIsNone(
            verify_history_candidate(CURRENT, candidate)
        )

    def test_rejects_missing_date(self):
        candidate = {
            **CANDIDATE,
            "published": "",
        }

        self.assertIsNone(
            verify_history_candidate(CURRENT, candidate)
        )

    def test_cleans_whitespace(self):
        self.assertEqual(
            clean_article_text("Hello   world\nagain"),
            "Hello world again",
        )

    def test_evidence_excerpt(self):
        excerpt = get_evidence_excerpt(
            ARTICLE_TEXT,
            {"openai", "agent"},
        )

        self.assertIn("OpenAI", excerpt)

    def test_removes_duplicates(self):
        results = verify_history_candidates(
            CURRENT,
            [CANDIDATE, CANDIDATE],
        )

        self.assertEqual(len(results), 1)

    def test_rejects_invalid_url(self):
        self.assertFalse(
            is_publisher_url("javascript:alert(1)")
        )

    def test_rejects_localhost(self):
        self.assertFalse(
            is_publisher_url("http://localhost/story")
        )


if __name__ == "__main__":
    unittest.main()
