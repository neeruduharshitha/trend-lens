
import unittest
from unittest.mock import patch

from src.history_timeline import (
    prepare_timeline_evidence,
    build_timeline_prompt,
    validate_timeline_response,
    generate_historical_timeline,
)


CURRENT = {
    "title": "Nvidia announces new AI chips for data centers",
    "published": "Fri, 13 Nov 2026 20:00:00 GMT",
}

EVIDENCE = {
    "status": "evidence_ready",
    "title": "Meta expands Nvidia chip agreement",
    "published": "Tue, 17 Feb 2026 08:00:00 GMT",
    "source": "CNBC",
    "publisher_url": "https://www.cnbc.com/example",
    "evidence_excerpt": (
        "Meta announced an expanded agreement to use Nvidia chips "
        "in its artificial intelligence data centers."
    ),
}


class TestHistoryTimeline(unittest.TestCase):

    def test_prepares_verified_evidence(self):
        result = prepare_timeline_evidence([EVIDENCE])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "source_1")

    def test_rejects_unverified_evidence(self):
        article = {**EVIDENCE, "status": "unverified"}
        self.assertEqual(prepare_timeline_evidence([article]), [])

    def test_rejects_duplicate_urls(self):
        result = prepare_timeline_evidence([EVIDENCE, EVIDENCE])
        self.assertEqual(len(result), 1)

    def test_rejects_invalid_urls(self):
        article = {
            **EVIDENCE,
            "publisher_url": "http://localhost/example",
        }
        self.assertEqual(prepare_timeline_evidence([article]), [])

    def test_rejects_missing_excerpt(self):
        article = {**EVIDENCE, "evidence_excerpt": ""}
        self.assertEqual(prepare_timeline_evidence([article]), [])

    def test_prompt_requests_source_ids_only(self):
        evidence = prepare_timeline_evidence([EVIDENCE])
        prompt = build_timeline_prompt(CURRENT, evidence)

        self.assertIn('"source_ids"', prompt)
        self.assertIn("Do not write summaries", prompt)

    def test_validates_source_selection(self):
        evidence = prepare_timeline_evidence([EVIDENCE])

        output = {"source_ids": ["source_1"]}
        result = validate_timeline_response(output, evidence)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["date"], "2026-02-17")
        self.assertEqual(
            result[0]["url"],
            "https://www.cnbc.com/example",
        )

    def test_rejects_invented_source(self):
        evidence = prepare_timeline_evidence([EVIDENCE])

        result = validate_timeline_response(
            {"source_ids": ["source_999"]},
            evidence,
        )

        self.assertEqual(result, [])

    def test_rejects_duplicate_source_ids(self):
        evidence = prepare_timeline_evidence([EVIDENCE])

        result = validate_timeline_response(
            {"source_ids": ["source_1", "source_1"]},
            evidence,
        )

        self.assertEqual(len(result), 1)

    def test_prevents_incorrect_direct_predecessor(self):
        evidence = prepare_timeline_evidence([EVIDENCE])

        result = validate_timeline_response(
            {
                "source_ids": ["source_1"],
                "entries": [
                    {
                        "source_id": "source_1",
                        "relationship": "direct_predecessor",
                    }
                ],
            },
            evidence,
        )

        self.assertEqual(
            result[0]["relationship"],
            "broader_industry_context",
        )

    def test_prevents_unsupported_causal_language(self):
        evidence = prepare_timeline_evidence([EVIDENCE])

        result = validate_timeline_response(
            {
                "source_ids": ["source_1"],
                "description": (
                    "This deal directly caused Nvidia's "
                    "next chip announcement."
                ),
            },
            evidence,
        )

        self.assertEqual(
            result[0]["description"],
            EVIDENCE["evidence_excerpt"],
        )

        self.assertNotIn(
            "directly caused",
            result[0]["description"],
        )

    def test_prevents_unsupported_details(self):
        evidence = prepare_timeline_evidence([EVIDENCE])

        result = validate_timeline_response(
            {
                "source_ids": ["source_1"],
                "description": (
                    "Meta signed a secret billion-dollar "
                    "agreement with Nvidia."
                ),
            },
            evidence,
        )

        self.assertEqual(
            result[0]["description"],
            EVIDENCE["evidence_excerpt"],
        )

    @patch("src.history_timeline.request_ollama")
    def test_generates_timeline(self, mock_ollama):
        mock_ollama.return_value = {
            "source_ids": ["source_1"]
        }

        result = generate_historical_timeline(
            CURRENT,
            [EVIDENCE],
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["date"], "2026-02-17")
        mock_ollama.assert_called_once()

    @patch("src.history_timeline.request_ollama")
    def test_no_evidence_skips_ollama(self, mock_ollama):
        result = generate_historical_timeline(CURRENT, [])

        self.assertEqual(result, [])
        mock_ollama.assert_not_called()

    @patch("src.history_timeline.request_ollama")
    def test_ollama_failure_returns_empty(self, mock_ollama):
        mock_ollama.side_effect = ValueError("Invalid JSON")

        result = generate_historical_timeline(
            CURRENT,
            [EVIDENCE],
        )

        self.assertEqual(result, [])

    @patch("src.history_timeline.request_ollama")
    def test_rejects_future_evidence(self, mock_ollama):
        future = {
            **EVIDENCE,
            "published": "Fri, 20 Nov 2026 08:00:00 GMT",
        }

        result = generate_historical_timeline(
            CURRENT,
            [future],
        )

        self.assertEqual(result, [])
        mock_ollama.assert_not_called()


if __name__ == "__main__":
    unittest.main()
