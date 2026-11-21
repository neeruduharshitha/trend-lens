
import re

from src.history_retriever import tokenize_title
from src.history_topics import extract_topics


EVENT_WORDS = {
    "announce", "announced", "announces",
    "announcement", "launch", "launched",
    "launches", "launching", "introduce",
    "introduced", "introduces", "unveil",
    "unveiled", "unveils", "release",
    "released", "releases", "reveals",
    "revealed", "new", "latest", "today",
    "now", "first", "report", "reports",
    "says", "said",
}

GENERAL_WORDS = {
    "technology", "tech", "company",
    "companies", "business", "industry",
    "users", "people", "platform",
    "product", "products", "feature",
    "features", "service", "services",
    "update", "updates", "her", "his",
    "their", "down", "winds", "wind",
    "targets", "target", "million",
    "billion",
}

TOPIC_TERMS = {
    "ai": {
        "ai", "artificial", "intelligence",
        "agents", "agent", "chatbot",
        "chatgpt", "llm", "model",
        "models", "automation",
    },
    "commerce": {
        "wallet", "payment", "payments",
        "purchase", "purchases", "shopping",
        "checkout", "commerce",
    },
    "cybersecurity": {
        "security", "cybersecurity",
        "ransomware", "malware", "hack",
        "hacking", "breach", "vulnerability",
    },
    "chips": {
        "chip", "chips", "semiconductor",
        "semiconductors", "gpu", "gpus",
        "processor", "processors",
    },
    "cloud": {
        "cloud", "datacenter", "datacenters",
        "infrastructure", "server", "servers",
    },
    "robotics": {
        "robot", "robots", "robotics",
        "autonomous", "drone", "drones",
    },
    "venture_capital": {
        "vc", "venture", "ventures", "capital",
        "invest", "investing", "investment",
        "investments", "investor", "investors",
        "fund", "funds", "funding", "startup",
        "startups", "seed", "portfolio",
    },
    "acquisitions": {
        "acquire", "acquired", "acquisition",
        "merger", "merges", "takeover",
        "buyout",
    },
}

TOPIC_SEARCH_LABELS = {
    "venture_capital": "venture capital",
    "acquisitions": "acquisition",
    "cybersecurity": "cybersecurity",
    "chips": "semiconductors",
    "ai": "artificial intelligence",
    "cloud": "cloud computing",
    "robotics": "robotics",
    "commerce": "digital commerce",
}


def meaningful_terms(title):
    if not isinstance(title, str):
        return []

    valid = tokenize_title(title)
    words = re.findall(r"[A-Za-z0-9]+", title)

    terms = []
    seen = set()

    for word in words:
        lower = word.lower()

        if lower not in valid:
            continue
        if lower in EVENT_WORDS:
            continue
        if lower in GENERAL_WORDS:
            continue
        if lower in seen:
            continue

        seen.add(lower)
        terms.append(word)

    return terms


def detect_topics(title):
    words = {word.lower() for word in meaningful_terms(title)}

    return [
        topic
        for topic, vocabulary in TOPIC_TERMS.items()
        if words & vocabulary
    ]


def extract_leading_entity(title):
    """
    Identify a likely headline subject from initial
    capitalized words. This is a search heuristic,
    not full named-entity recognition.
    """
    if not isinstance(title, str):
        return ""

    words = re.findall(r"[A-Za-z0-9]+", title)
    entity = []

    for word in words:
        if (
            word[0].isupper()
            or (word.isupper() and len(word) >= 2)
        ):
            entity.append(word)
        else:
            break

        if len(entity) >= 3:
            break

    return " ".join(entity)


def generate_historical_queries(title, max_queries=4):
    if not isinstance(title, str) or not title.strip():
        return []

    if max_queries <= 0:
        return []

    terms = meaningful_terms(title)

    if not terms:
        return []

    queries = []
    seen = set()

    def add_query(value):
        value = " ".join(value.split())

        if not value:
            return

        normalized = value.lower()

        if normalized not in seen:
            seen.add(normalized)
            queries.append(value)

    entity = extract_leading_entity(title)
    topics = detect_topics(title)

    # 1. Search the primary subject and its topic.
    if entity and topics:
        topic_label = TOPIC_SEARCH_LABELS.get(
            topics[0], topics[0].replace("_", " ")
        )
        add_query(f"{entity} {topic_label}")

    # 2. Search a compact headline-derived query.
    add_query(" ".join(terms[:5]))

    # 3. Search the subject with the next useful term.
    if entity:
        entity_words = set(entity.lower().split())
        remainder = [
            term for term in terms
            if term.lower() not in entity_words
        ]
        if remainder:
            add_query(f"{entity} {remainder[0]}")

    # 4. Search the underlying topic.
    if len(terms) >= 3:
        add_query(" ".join(terms[:3]))

    if topics:
        topic_words = [
            term for term in terms
            if any(
                term.lower() in TOPIC_TERMS[topic]
                for topic in topics
            )
        ]
        if topic_words:
            add_query(" ".join(topic_words[:4]))

    if len(terms) >= 4:
        add_query(" ".join(terms[-4:]))

    return queries[:max_queries]


def historical_topic_score(current_title, candidate_title):
    """
    Score headline overlap and shared topics.

    A person's name alone must not make an unrelated
    article historically relevant.
    """
    current_terms = {
        word.lower()
        for word in meaningful_terms(current_title)
    }
    candidate_terms = {
        word.lower()
        for word in meaningful_terms(candidate_title)
    }

    if not current_terms or not candidate_terms:
        return 0.0

    overlap = current_terms & candidate_terms

    current_topics = set(detect_topics(current_title))
    candidate_topics = set(detect_topics(candidate_title))

    shared_topics = current_topics & candidate_topics

    broad_shared = (
        extract_topics(current_title)
        & extract_topics(candidate_title)
    )

    # Prevent a shared person's name from being
    # sufficient when topics are unrelated.
    if not shared_topics and not broad_shared:
        return 0.0

    direct_score = len(overlap) / len(current_terms)

    topic_score = (
        len(shared_topics) / len(current_topics)
        if current_topics
        else 0.0
    )

    broad_score = (
        len(broad_shared) / len(extract_topics(current_title))
        if extract_topics(current_title)
        else 0.0
    )

    return round(
        0.45 * direct_score
        + 0.35 * topic_score
        + 0.20 * broad_score,
        3,
    )
