import unittest
from unittest.mock import patch

from src.collector import fetch_news


class TestNewsCollector(unittest.TestCase):

    def test_skips_articles_missing_title_or_link(self):
        fake_entries = [
            {"title": "Valid AI article", "link": "https://example.com/ai"},
            {"title": "", "link": "https://example.com/missing-title"},
            {"title": "Missing URL"},
        ]

        with patch("src.collector.feedparser.parse") as mock_parse:
            mock_parse.return_value.entries = fake_entries
            articles = fetch_news("https://example.com/feed")

        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["title"], "Valid AI article")
        self.assertEqual(articles[0]["link"], "https://example.com/ai")

    def test_skips_duplicate_articles(self):
        fake_entries = [
            {
                "title": "AI Agent Launch",
                "link": "https://example.com/ai-agent",
            },
            {
                "title": "AI Agent Launch",
                "link": "https://example.com/ai-agent",
            },
            {
                "title": "New AI Model Released",
                "link": "https://example.com/new-model",
            },
        ]

        with patch("src.collector.feedparser.parse") as mock_parse:
            mock_parse.return_value.entries = fake_entries
            articles = fetch_news("https://example.com/feed")

        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0]["title"], "AI Agent Launch")
        self.assertEqual(articles[1]["title"], "New AI Model Released")