
from src.historical_queries import (
    generate_historical_queries,
    historical_topic_score,
)
from src.history_topics import (
    extract_topics,
    topic_relevance,
)


SERENA_CURRENT = (
    "Serena Williams winds down her VC firm, "
    "launches new fund, targets $200M"
)

SERENA_RELEVANT = (
    "Serena Ventures raises $111 million "
    "to invest in early-stage startups"
)

SERENA_UNRELATED = (
    "Serena Williams returns to tennis training"
)

CHIP_CURRENT = (
    "Nvidia AI chips face new China export controls"
)

CHIP_RELEVANT = (
    "US expands restrictions on Nvidia chips to China"
)


def test_venture_capital_topic_detection():
    assert "venture_capital" in extract_topics(
        "Serena Ventures investment fund"
    )


def test_venture_capital_queries_preserve_subject():
    queries = generate_historical_queries(
        SERENA_CURRENT
    )

    assert queries
    assert any(
        "Serena Williams" in query
        for query in queries
    )
    assert any(
        "venture capital" in query.lower()
        for query in queries
    )


def test_relevant_investment_story_scores_positive():
    score = historical_topic_score(
        SERENA_CURRENT,
        SERENA_RELEVANT,
    )

    assert score >= 0.15


def test_unrelated_tennis_story_rejected():
    score = historical_topic_score(
        SERENA_CURRENT,
        SERENA_UNRELATED,
    )

    assert score == 0.0


def test_venture_capital_topic_relevance():
    score = topic_relevance(
        SERENA_CURRENT,
        SERENA_RELEVANT,
    )

    assert score > 0.0


def test_chip_history_still_matches():
    score = max(
        historical_topic_score(
            CHIP_CURRENT,
            CHIP_RELEVANT,
        ),
        topic_relevance(
            CHIP_CURRENT,
            CHIP_RELEVANT,
            ),
    )

    assert score >= 0.15


def test_queries_do_not_invent_company_name():
    queries = generate_historical_queries(
        SERENA_CURRENT
    )

    assert not any(
        "Starfire Ventures" in query
        for query in queries
    )


def test_invalid_query_input():
    assert generate_historical_queries("") == []
    assert generate_historical_queries(None) == []
    assert generate_historical_queries("Test", max_queries=0) == []
