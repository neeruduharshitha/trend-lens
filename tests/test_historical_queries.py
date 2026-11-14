
import unittest

from src.historical_queries import (
    meaningful_terms,
    detect_topics,
    generate_historical_queries,
    historical_topic_score,
)


class TestHistoricalQueries(unittest.TestCase):

    def test_empty_title(self):
        self.assertEqual(
            generate_historical_queries(""),
            [],
        )

    def test_removes_announcement_language(self):
        terms = meaningful_terms(
            "OpenAI launches ChatGPT Wallet"
        )

        self.assertNotIn("launches", [
            term.lower() for term in terms
        ])

    def test_detects_ai_and_commerce(self):
        topics = detect_topics(
            "ChatGPT AI agents shopping payments"
        )

        self.assertIn("ai", topics)
        self.assertIn("commerce", topics)

    def test_generates_multiple_queries(self):
        queries = generate_historical_queries(
            "OpenAI launches ChatGPT Wallet AI agents"
        )

        self.assertGreaterEqual(len(queries), 2)

    def test_queries_are_unique(self):
        queries = generate_historical_queries(
            "OpenAI launches ChatGPT Wallet AI agents"
        )

        self.assertEqual(
            len(queries),
            len(set(query.lower() for query in queries)),
        )

    def test_query_limit(self):
        queries = generate_historical_queries(
            "OpenAI launches ChatGPT Wallet AI agents",
            max_queries=2,
        )

        self.assertLessEqual(len(queries), 2)

    def test_related_topics_score_higher(self):
        current = (
            "OpenAI launches ChatGPT Wallet "
            "for AI agent shopping"
        )

        related = (
            "Visa expands AI agent shopping payments"
        )

        unrelated = (
            "New smartphone camera improves photography"
        )

        self.assertGreater(
            historical_topic_score(current, related),
            historical_topic_score(current, unrelated),
        )

    def test_unrelated_topic_scores_zero(self):
        self.assertEqual(
            historical_topic_score(
                "AI agents shopping payments",
                "Space telescope discovers galaxy",
            ),
            0.0,
        )


if __name__ == "__main__":
    unittest.main()
