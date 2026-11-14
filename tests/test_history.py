
import unittest

from src.history_retriever import (
    find_related_history,
    normalize_url,
    parse_article_date,
    relevance_score,
)


CURRENT_ARTICLE = {
    "title": "OpenAI announces new AI agent platform",
    "link": "https://example.com/current",
    "published": "Fri, 13 Nov 2026 15:00:00 GMT",
}


def make_article(title, url, published):
    return {
        "title": title,
        "link": url,
        "published": published,
    }


class TestHistoryRetriever(unittest.TestCase):
    def test_preserves_source_name(self):
        current = {
            "title": "OpenAI announces new AI agent platform",
            "link": "https://example.com/current",
            "published": "Fri, 13 Nov 2026 20:00:00 GMT",
        }

        candidates = [{
            "title": "OpenAI introduces AI agent tools",
            "link": "https://news.google.com/rss/articles/example",
            "published": "Thu, 12 Nov 2026 15:00:00 GMT",
            "source": "TechCrunch",
        }]

        results = find_related_history(
            current,
            candidates,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source"], "TechCrunch")

    def test_relevant_earlier_article(self):
        candidates = [
            make_article(
                "OpenAI introduces AI agent tools",
                "https://example.com/earlier",
                "Thu, 12 Nov 2026 15:00:00 GMT",
            )
        ]

        result = find_related_history(
            CURRENT_ARTICLE,
            candidates,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(
            result[0]["link"],
            "https://example.com/earlier",
        )

    def test_rejects_future_article(self):
        candidates = [
            make_article(
                "OpenAI introduces AI agent tools",
                "https://example.com/future",
                "Sat, 14 Nov 2026 15:00:00 GMT",
            )
        ]

        result = find_related_history(
            CURRENT_ARTICLE,
            candidates,
        )

        self.assertEqual(result, [])

    def test_rejects_missing_date(self):
        candidates = [
            make_article(
                "OpenAI introduces AI agent tools",
                "https://example.com/no-date",
                "",
            )
        ]

        result = find_related_history(
            CURRENT_ARTICLE,
            candidates,
        )

        self.assertEqual(result, [])

    def test_rejects_unrelated_article(self):
        candidates = [
            make_article(
                "Scientists discover new ocean species",
                "https://example.com/ocean",
                "Thu, 12 Nov 2026 15:00:00 GMT",
            )
        ]

        result = find_related_history(
            CURRENT_ARTICLE,
            candidates,
        )

        self.assertEqual(result, [])

    def test_rejects_current_article(self):
        candidates = [
            make_article(
                "OpenAI announces new AI agent platform",
                "https://example.com/current",
                "Thu, 12 Nov 2026 15:00:00 GMT",
            )
        ]

        result = find_related_history(
            CURRENT_ARTICLE,
            candidates,
        )

        self.assertEqual(result, [])

    def test_removes_duplicate_urls(self):
        candidates = [
            make_article(
                "OpenAI introduces AI agent tools",
                "https://example.com/earlier",
                "Thu, 12 Nov 2026 15:00:00 GMT",
            ),
            make_article(
                "OpenAI introduces AI agent tools",
                "https://example.com/earlier?utm_source=rss",
                "Thu, 12 Nov 2026 15:00:00 GMT",
            ),
        ]

        result = find_related_history(
            CURRENT_ARTICLE,
            candidates,
        )

        self.assertEqual(len(result), 1)

    def test_normalize_url(self):
        self.assertEqual(
            normalize_url(
                "https://www.example.com/story/?utm_source=rss"
            ),
            "https://example.com/story",
        )

    def test_parse_rss_date(self):
        result = parse_article_date(
            "Thu, 12 Nov 2026 15:00:00 GMT"
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2026)

    def test_parse_iso_date(self):
        result = parse_article_date(
            "2026-11-12T15:00:00Z"
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2026)

    def test_relevance_score(self):
        score = relevance_score(
            "OpenAI announces new AI agent platform",
            "OpenAI introduces AI agent tools",
        )

        self.assertGreaterEqual(score, 0.35)


if __name__ == "__main__":
    unittest.main()
