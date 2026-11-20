
import unittest
from unittest.mock import patch

from src.history_ui import (
    format_timeline_date,
    get_historical_timeline,
)


ARTICLE = {
    "title": "Nvidia announces new AI chips",
    "link": "https://techcrunch.com/example",
    "published": "Fri, 13 Nov 2026 20:00:00 GMT",
}

EVIDENCE = [
    {
        "status": "evidence_ready",
        "title": "Earlier Nvidia development",
        "published": "Tue, 17 Feb 2026 08:00:00 GMT",
        "source": "CNBC",
        "publisher_url": "https://www.cnbc.com/example",
        "evidence_excerpt": "Earlier reporting on Nvidia chips.",
    }
]

TIMELINE = [
    {
        "date": "2026-02-17",
        "title": "Earlier Nvidia development",
        "description": "Earlier reporting on Nvidia chips.",
        "relationship": "broader_industry_context",
        "source": "CNBC",
        "url": "https://www.cnbc.com/example",
    }
]


class TestHistoryUI(unittest.TestCase):

    def setUp(self):
        get_historical_timeline.clear()

    def tearDown(self):
        get_historical_timeline.clear()

    def test_formats_timeline_date(self):
        self.assertEqual(
            format_timeline_date("2026-02-17"),
            "Feb 17, 2026",
        )

    def test_handles_invalid_date(self):
        self.assertEqual(
            format_timeline_date("invalid"),
            "invalid",
        )

    @patch("src.history_ui.generate_historical_timeline")
    @patch("src.history_ui.build_historical_evidence")
    def test_retrieves_and_generates_timeline(
        self,
        mock_retrieve,
        mock_generate,
    ):
        mock_retrieve.return_value = EVIDENCE
        mock_generate.return_value = TIMELINE

        result = get_historical_timeline(
            ARTICLE["title"],
            ARTICLE["link"],
            ARTICLE["published"],
        )

        self.assertEqual(result, TIMELINE)
        mock_retrieve.assert_called_once()
        mock_generate.assert_called_once()

    @patch("src.history_ui.generate_historical_timeline")
    @patch("src.history_ui.build_historical_evidence")
    def test_skips_generation_without_evidence(
        self,
        mock_retrieve,
        mock_generate,
    ):
        mock_retrieve.return_value = []

        result = get_historical_timeline(
            ARTICLE["title"],
            ARTICLE["link"],
            ARTICLE["published"],
        )

        self.assertEqual(result, [])
        mock_generate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
