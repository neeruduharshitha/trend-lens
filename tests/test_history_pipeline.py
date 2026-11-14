
import unittest
from unittest.mock import patch

from src.historical_queries import generate_historical_queries
from src.history_pipeline import (
    build_historical_evidence,
    build_historical_query,
    sufficiently_historical,
    title_similarity,
    diversify_history,
)


# ---------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------

CURRENT = {
    "title": "OpenAI announces new AI agent platform",
    "link": "https://techcrunch.com/current",
    "published": "Fri, 13 Nov 2026 20:00:00 GMT",
}

GOOGLE_URL = (
    "https://news.google.com/rss/articles/example"
)

CANDIDATE = {
    "title": "OpenAI introduces AI agent tools",
    "link": GOOGLE_URL,
    "published": "Thu, 29 Oct 2026 15:00:00 GMT",
    "source": "TechCrunch",
}

RESOLVED = {
    **CANDIDATE,
    "publisher_url": "https://techcrunch.com/example",
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


class TestHistoryPipeline(unittest.TestCase):

    # -----------------------------------------------------
    # 1. Successful pipeline
    # -----------------------------------------------------

    @patch("src.history_pipeline.extract_publisher_article")
    @patch("src.history_pipeline.resolve_publisher_links")
    @patch("src.history_pipeline.search_related_news")
    def test_successful_pipeline(
        self,
        mock_search,
        mock_resolve,
        mock_extract,
    ):
        mock_search.return_value = [CANDIDATE]
        mock_resolve.return_value = [RESOLVED]
        mock_extract.return_value = ARTICLE_TEXT

        results = build_historical_evidence(CURRENT)

        self.assertEqual(len(results), 1)

        self.assertEqual(
            results[0]["status"],
            "evidence_ready",
        )

        mock_extract.assert_called_once()

    # -----------------------------------------------------
    # 2. No search results
    # -----------------------------------------------------

    @patch("src.history_pipeline.search_related_news")
    def test_no_search_results(self, mock_search):
        mock_search.return_value = []

        self.assertEqual(
            build_historical_evidence(CURRENT),
            [],
        )

    # -----------------------------------------------------
    # 3. No resolved publisher links
    # -----------------------------------------------------

    @patch("src.history_pipeline.resolve_publisher_links")
    @patch("src.history_pipeline.search_related_news")
    def test_no_resolved_links(
        self,
        mock_search,
        mock_resolve,
    ):
        mock_search.return_value = [CANDIDATE]
        mock_resolve.return_value = []

        self.assertEqual(
            build_historical_evidence(CURRENT),
            [],
        )

    # -----------------------------------------------------
    # 4. Future articles must be rejected
    # -----------------------------------------------------

    @patch("src.history_pipeline.resolve_publisher_links")
    @patch("src.history_pipeline.search_related_news")
    def test_rejects_future_articles(
        self,
        mock_search,
        mock_resolve,
    ):
        future = {
            **CANDIDATE,
            "published": "Sat, 14 Nov 2026 15:00:00 GMT",
        }

        mock_search.return_value = [future]

        self.assertEqual(
            build_historical_evidence(CURRENT),
            [],
        )

        mock_resolve.assert_not_called()

    # -----------------------------------------------------
    # 5. Invalid current article
    # -----------------------------------------------------

    def test_invalid_article(self):
        self.assertEqual(
            build_historical_evidence({}),
            [],
        )

    # -----------------------------------------------------
    # 6. Historical query removes launch words
    # -----------------------------------------------------

    def test_historical_query_removes_launch_words(self):
        query = build_historical_query(
            "OpenAI launches ChatGPT Wallet AI agents"
        )

        self.assertEqual(
            query,
            "OpenAI ChatGPT Wallet agents",
        )

    # -----------------------------------------------------
    # 7. Older articles are accepted
    # -----------------------------------------------------

    def test_accepts_older_article(self):
        self.assertTrue(
            sufficiently_historical(
                CURRENT,
                CANDIDATE,
                min_age_days=7,
            )
        )

    # -----------------------------------------------------
    # 8. Recent articles are rejected
    # -----------------------------------------------------

    def test_rejects_recent_article(self):
        recent = {
            **CANDIDATE,
            "published": "Thu, 12 Nov 2026 15:00:00 GMT",
        }

        self.assertFalse(
            sufficiently_historical(
                CURRENT,
                recent,
                min_age_days=7,
            )
        )

    # -----------------------------------------------------
    # 9. Future publication dates are rejected
    # -----------------------------------------------------

    def test_rejects_future_article_date(self):
        future = {
            **CANDIDATE,
            "published": "Sat, 14 Nov 2026 15:00:00 GMT",
        }

        self.assertFalse(
            sufficiently_historical(
                CURRENT,
                future,
                min_age_days=0,
            )
        )

    # -----------------------------------------------------
    # 10. Identical headlines have full similarity
    # -----------------------------------------------------

    def test_identical_titles_have_full_similarity(self):
        self.assertEqual(
            title_similarity(
                "OpenAI introduces AI agents",
                "OpenAI introduces AI agents",
            ),
            1.0,
        )

    # -----------------------------------------------------
    # 11. Duplicate headlines are removed
    # -----------------------------------------------------

    def test_diversify_removes_duplicate_titles(self):
        candidates = [
            {
                "title": "OpenAI introduces AI agent tools",
                "link": "https://example.com/one",
            },
            {
                "title": "OpenAI introduces AI agent tools",
                "link": "https://example.com/two",
            },
            {
                "title": "Google releases Gemini update",
                "link": "https://example.com/three",
            },
        ]

        results = diversify_history(candidates)

        self.assertEqual(len(results), 2)

    # -----------------------------------------------------
    # 12. Recent candidates never reach URL resolution
    # -----------------------------------------------------

    @patch("src.history_pipeline.resolve_publisher_links")
    @patch("src.history_pipeline.search_related_news")
    def test_recent_candidates_not_resolved(
        self,
        mock_search,
        mock_resolve,
    ):
        recent = {
            **CANDIDATE,
            "published": "Thu, 12 Nov 2026 15:00:00 GMT",
        }

        mock_search.return_value = [recent]

        results = build_historical_evidence(
            CURRENT,
            min_age_days=7,
        )

        self.assertEqual(results, [])

        mock_resolve.assert_not_called()

    # -----------------------------------------------------
    # 13. Search includes broader historical topics
    # -----------------------------------------------------

    @patch("src.history_pipeline.search_related_news")
    def test_searches_broader_topic(
        self,
        mock_search,
    ):
        mock_search.return_value = []

        build_historical_evidence(CURRENT)

        searched_queries = [
            call.args[0]
            for call in mock_search.call_args_list
        ]

        # Original headline must be searched.
        self.assertIn(
            CURRENT["title"],
            searched_queries,
        )

        # New historical query generator must be used.
        historical_queries = generate_historical_queries(
            CURRENT["title"],
            max_queries=4,
        )

        self.assertTrue(
            any(
                query in searched_queries
                for query in historical_queries
            )
        )


if __name__ == "__main__":
    unittest.main()
