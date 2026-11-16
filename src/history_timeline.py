
import json
from datetime import datetime
from urllib.parse import urlsplit

import requests

from src.history_retriever import parse_article_date


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_MODEL = "qwen2.5:3b"

BROADER_CONTEXT = "broader_industry_context"


def prepare_timeline_evidence(evidence, limit=5):
    """Prepare verified, source-backed historical evidence."""
    if not isinstance(evidence, list) or limit < 1:
        return []

    prepared = []
    seen_urls = set()

    for article in evidence:
        if not isinstance(article, dict):
            continue

        if article.get("status") != "evidence_ready":
            continue

        url = article.get("publisher_url")
        title = article.get("title")
        source = article.get("source")
        excerpt = article.get("evidence_excerpt")
        published = parse_article_date(article.get("published"))

        if not all(
            isinstance(value, str) and value.strip()
            for value in (url, title, source, excerpt)
        ):
            continue

        if not published:
            continue

        try:
            parts = urlsplit(url)
            valid_url = (
                parts.scheme == "https"
                and bool(parts.hostname)
                and not parts.username
                and not parts.password
            )
        except ValueError:
            continue

        if not valid_url or url in seen_urls:
            continue

        # Use the retrieved evidence verbatim.
        # Do not let the language model rewrite factual claims.
        clean_excerpt = " ".join(excerpt.split())

        prepared.append(
            {
                "title": title.strip(),
                "date": published.date().isoformat(),
                "published_utc": published,
                "source": source.strip(),
                "url": url,
                "excerpt": clean_excerpt,
            }
        )
        seen_urls.add(url)

    # Select the earliest historical records before assigning IDs.
    prepared.sort(key=lambda item: item["published_utc"])
    prepared = prepared[:limit]

    for index, item in enumerate(prepared, 1):
        item["id"] = f"source_{index}"
        del item["published_utc"]

    return prepared


def build_timeline_prompt(current_article, evidence):
    """Ask Ollama to select relevant sources, not invent summaries."""
    model_sources = [
        {
            "id": item["id"],
            "title": item["title"],
            "date": item["date"],
            "excerpt": item["excerpt"],
        }
        for item in evidence
    ]

    payload = {
        "current_headline": current_article["title"],
        "historical_sources": model_sources,
    }

    return (
        "You are selecting historical news sources for a technology "
        "news application.\n\n"
        "Your ONLY task is to select relevant source IDs.\n"
        "Do not write summaries, explanations, dates, or citations.\n"
        "Do not infer that an earlier event caused the current news.\n"
        "Prefer sources describing earlier developments relevant "
        "to the current headline.\n"
        "Exclude sources that only share generic words such as AI "
        "or technology without meaningful topical relevance.\n"
        "Return ONLY a JSON object in this format:\n"
        '{"source_ids": ["source_1", "source_2"]}\n\n'
        f"INPUT:\n{json.dumps(payload, ensure_ascii=False)}"
    )


def request_ollama(prompt, model=DEFAULT_MODEL, timeout=120):
    """Request structured output from local Ollama."""
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
        },
        timeout=timeout,
    )

    response.raise_for_status()
    payload = response.json()

    return json.loads(payload["response"])


def validate_timeline_response(model_output, evidence):
    """Accept only valid source selections and trusted source content."""
    if not isinstance(model_output, dict):
        return []

    source_ids = model_output.get("source_ids")

    if not isinstance(source_ids, list):
        return []

    sources_by_id = {item["id"]: item for item in evidence}
    validated = []
    seen_ids = set()

    for source_id in source_ids:
        if not isinstance(source_id, str):
            continue

        if source_id not in sources_by_id:
            continue

        if source_id in seen_ids:
            continue

        source = sources_by_id[source_id]

        validated.append(
            {
                "date": source["date"],
                "title": source["title"],
                "description": source["excerpt"],
                "relationship": BROADER_CONTEXT,
                "source": source["source"],
                "url": source["url"],
            }
        )

        seen_ids.add(source_id)

    return sorted(validated, key=lambda item: item["date"])


def generate_historical_timeline(
    current_article,
    evidence,
    model=DEFAULT_MODEL,
):
    """Generate a conservative, source-grounded historical timeline."""
    if not isinstance(current_article, dict):
        return []

    title = current_article.get("title")
    current_date = parse_article_date(current_article.get("published"))

    if not isinstance(title, str) or not title.strip():
        return []

    if not current_date:
        return []

    prepared = prepare_timeline_evidence(evidence)

    # Compare complete UTC timestamps, not just calendar dates.
    # Evidence from later on the same day must also be rejected.
    prepared = [
        item
        for item in prepared
        if datetime.fromisoformat(
            item["date"]
        ).date() < current_date.date()
    ]

    if not prepared:
        return []

    prompt = build_timeline_prompt(current_article, prepared)

    try:
        model_output = request_ollama(prompt, model=model)
    except (
        requests.RequestException,
        ValueError,
        KeyError,
        TypeError,
    ):
        return []

    return validate_timeline_response(model_output, prepared)
