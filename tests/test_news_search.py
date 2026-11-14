
import unittest
from unittest.mock import patch
from io import BytesIO

from src.news_search import (
    build_search_query,
    search_google_news,
    search_related_news,
)


SAMPLE_RSS = b"""
<rss version="2.0">
  <channel>
    <item>
      <title>OpenAI introduces AI agent tools</title>
      <link>https://example.com/story1</link>
      <pubDate>Thu, 12 Nov 2026 15:00:00 GMT</pubDate>
      <source>Example News</source>
    </item>
    <item>
      <title>OpenAI announces agent improvements</title>
      <link>https://example.com/story2</link>
      <pubDate>Wed, 11 Nov 2026 15:00:00 GMT</pubDate>
      <source>Technology Daily</source>
    </item>
  </channel>
</rss>
"""


class TestNewsSearch(unittest.TestCase):

    def test_build_search_query(self):
        query = build_search_query(
            "OpenAI announces new AI agent platform"
        )

        self.assertIn("OpenAI", query)
        self.assertIn("agent", query)
        self.assertNotIn("new", query.split())

    @patch("src.news_search.urllib.request.urlopen")
    def test_successful_search(self, mock_urlopen):
        mock_urlopen.return_value.__enter__.return_value = (
            BytesIO(SAMPLE_RSS)
        )

        articles = search_google_news("OpenAI agents")

        self.assertEqual(len(articles), 2)
        self.assertEqual(
            articles[0]["source"],
            "Example News",
        )

    @patch("src.news_search.urllib.request.urlopen")
    def test_max_results(self, mock_urlopen):
        mock_urlopen.return_value.__enter__.return_value = (
            BytesIO(SAMPLE_RSS)
        )

        articles = search_google_news(
            "OpenAI agents",
            max_results=1,
        )

        self.assertEqual(len(articles), 1)

    def test_empty_query(self):
        self.assertEqual(search_google_news(""), [])

    @patch("src.news_search.search_google_news")
    def test_related_news_search(self, mock_search):
        mock_search.return_value = []

        search_related_news(
            "OpenAI announces new AI agent platform"
        )

        mock_search.assert_called_once()

        query = mock_search.call_args.kwargs["query"]

        self.assertIn("OpenAI", query)

    @patch("src.news_search.urllib.request.urlopen")
    def test_invalid_xml(self, mock_urlopen):
        mock_urlopen.return_value.__enter__.return_value = (
            BytesIO(b"invalid xml")
        )

        with self.assertRaises(RuntimeError):
            search_google_news("OpenAI agents")


if __name__ == "__main__":
    unittest.main()
