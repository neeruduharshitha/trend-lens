
import unittest

from src.history_topics import (
    extract_topics,
    topic_relevance,
)


class TestHistoryTopics(unittest.TestCase):

    def setUp(self):
        self.current = (
            "US tightens AI chip export controls "
            "to deter Chinese companies from "
            "accessing compute remotely"
        )

    def test_related_export_controls(self):
        candidate = (
            "Nvidia chip export restrictions "
            "on China expand"
        )

        self.assertGreaterEqual(
            topic_relevance(self.current, candidate),
            0.5,
        )

    def test_related_remote_access(self):
        candidate = (
            "Chinese AI lab uses Nvidia Blackwell "
            "chips through European cloud infrastructure"
        )

        self.assertGreaterEqual(
            topic_relevance(self.current, candidate),
            0.5,
        )

    def test_unrelated_nvidia_gaming(self):
        candidate = (
            "Nvidia launches gaming graphics card "
            "for PC enthusiasts"
        )

        self.assertLess(
            topic_relevance(self.current, candidate),
            0.35,
        )

    def test_unrelated_china_story(self):
        candidate = (
            "China announces new tourism campaign"
        )

        self.assertLess(
            topic_relevance(self.current, candidate),
            0.35,
        )

    def test_unrelated_ai_story(self):
        candidate = (
            "AI startup releases a new chatbot"
        )

        self.assertEqual(
            topic_relevance(self.current, candidate),
            0.0,
        )

    def test_topic_extraction(self):
        topics = extract_topics(
            "Nvidia GPUs under export controls in China"
        )

        self.assertIn("ai_chips", topics)
        self.assertIn("export_restrictions", topics)
        self.assertIn("china", topics)


if __name__ == "__main__":
    unittest.main()
