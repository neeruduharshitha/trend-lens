
import json
import unittest
from unittest.mock import patch
from urllib.error import URLError

from src.ai_explainer import (
    clean_terms,
    explain_article,
    validate_explanation,
)


# --------------------------------------------------
# Sample valid AI explanation
# --------------------------------------------------

VALID_EXPLANATION = {
    "what_happened": "A company announced a new product.",
    "why_it_matters": "The product could help developers.",
    "terms_to_know": [
        {
            "term": "AI agent",
            "meaning": "Software that uses AI to perform tasks.",
        }
    ],
    "whats_different_now": {
        "before": "The product was unavailable.",
        "after": "The product has been announced.",
        "explanation": "The announcement introduces a new option.",
    },
    "open_questions": [
        "When will the product become available?"
    ],
}


# --------------------------------------------------
# Fake HTTP response for testing Ollama
# --------------------------------------------------

class FakeResponse:
    """Simulate a response from the Ollama API."""

    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self, *args, **kwargs):
        return json.dumps(self.payload).encode("utf-8")


# --------------------------------------------------
# AI explainer unit tests
# --------------------------------------------------

class TestAIExplainer(unittest.TestCase):

    # ----------------------------------------------
    # Test 1: Valid explanation
    # ----------------------------------------------

    def test_valid_explanation(self):
        self.assertTrue(
            validate_explanation(VALID_EXPLANATION)
        )

    # ----------------------------------------------
    # Test 2: Missing required field
    # ----------------------------------------------

    def test_missing_field(self):
        invalid = VALID_EXPLANATION.copy()
        invalid.pop("open_questions")

        self.assertFalse(
            validate_explanation(invalid)
        )

    # ----------------------------------------------
    # Test 3: Invalid terminology structure
    # ----------------------------------------------

    def test_invalid_terms(self):
        invalid = VALID_EXPLANATION.copy()
        invalid["terms_to_know"] = ["AI agent"]

        self.assertFalse(
            validate_explanation(invalid)
        )

    # ----------------------------------------------
    # Test 4: Remove duplicate acronym
    # ----------------------------------------------

    def test_duplicate_acronym_removed(self):
        terms = [
            {
                "term": "Ocean Thermal Energy Conversion (OTEC)",
                "meaning": (
                    "Electricity from ocean "
                    "temperature differences."
                ),
            },
            {
                "term": "OTEC",
                "meaning": "Ocean thermal energy conversion.",
            },
        ]

        result = clean_terms(terms)

        self.assertEqual(len(result), 1)

        self.assertEqual(
            result[0]["term"],
            "Ocean Thermal Energy Conversion (OTEC)",
        )

    # ----------------------------------------------
    # Test 5: Remove empty terminology
    # ----------------------------------------------

    def test_empty_terms_removed(self):
        terms = [
            {
                "term": "",
                "meaning": "Empty",
            },
            {
                "term": "AI agent",
                "meaning": "Software that performs tasks.",
            },
            {
                "term": "Data center",
                "meaning": "",
            },
        ]

        result = clean_terms(terms)

        self.assertEqual(len(result), 1)

        self.assertEqual(
            result[0]["term"],
            "AI agent",
        )

    # ----------------------------------------------
    # Test 6: Successful AI generation
    # ----------------------------------------------

    @patch("src.ai_explainer.request.urlopen")
    def test_successful_generation(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(
            {
                "done_reason": "stop",
                "message": {
                    "content": json.dumps(
                        VALID_EXPLANATION
                    )
                },
            }
        )

        result = explain_article(
            "New AI product",
            (
                "A technology company announced a new "
                "AI product for developers. "
            ) * 5,
        )

        self.assertEqual(
            result,
            VALID_EXPLANATION,
        )

        mock_urlopen.assert_called_once()

    # ----------------------------------------------
    # Test 7: Ollama connection failure
    # ----------------------------------------------

    @patch("src.ai_explainer.request.urlopen")
    def test_connection_failure(self, mock_urlopen):
        mock_urlopen.side_effect = URLError(
            "Connection refused"
        )

        result = explain_article(
            "New AI product",
            (
                "A technology company announced a new "
                "AI product for developers. "
            ) * 5,
        )

        self.assertIsNone(result)

    # ----------------------------------------------
    # Test 8: Incomplete AI generation
    # ----------------------------------------------

    @patch("src.ai_explainer.request.urlopen")
    def test_incomplete_generation(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(
            {
                "done_reason": "length",
                "message": {
                    "content": "{}"
                },
            }
        )

        result = explain_article(
            "New AI product",
            (
                "A technology company announced a new "
                "AI product for developers. "
            ) * 5,
        )

        self.assertIsNone(result)


# --------------------------------------------------
# Run tests directly
# --------------------------------------------------

if __name__ == "__main__":
    unittest.main()
