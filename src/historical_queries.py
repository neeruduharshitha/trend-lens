
import re

from src.history_retriever import tokenize_title


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
    "update", "updates",
}

# Topic vocabulary, not hardcoded search queries.
# These terms describe broad technology areas.
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
        "shop", "checkout", "buy",
        "buying", "commerce",
    },
    "cybersecurity": {
        "security", "cybersecurity",
        "ransomware", "malware", "hack",
        "hacking", "breach", "attacks",
        "vulnerability",
    },
    "chips": {
        "chip", "chips", "semiconductor",
        "semiconductors", "gpu", "gpus",
        "processor", "processors",
    },
    "cloud": {
        "cloud", "datacenter",
        "datacenters", "infrastructure",
        "server", "servers",
    },
    "robotics": {
        "robot", "robots", "robotics",
        "autonomous", "drone", "drones",
    },
}


def meaningful_terms(title):
    if not isinstance(title, str):
        return []

    words = re.findall(r"[A-Za-z0-9]+", title)

    terms = []
    seen = set()

    for word in words:
        lower = word.lower()

        if len(lower) < 3:
            continue

        if lower in EVENT_WORDS:
            continue

        if lower in GENERAL_WORDS:
            continue

        if lower not in tokenize_title(title):
            continue

        if lower in seen:
            continue

        seen.add(lower)
        terms.append(word)

    return terms


def detect_topics(title):
    words = set(meaningful_terms(title))
    words = {word.lower() for word in words}

    return [
        topic
        for topic, vocabulary in TOPIC_TERMS.items()
        if words & vocabulary
    ]


def generate_historical_queries(title, max_queries=4):
    """
    Generate several search angles without
    inventing historical events.

    Returns keyword queries only.
    """

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

        if normalized in seen:
            return

        seen.add(normalized)
        queries.append(value)

    # Main topic, without announcement language.
    add_query(" ".join(terms[:6]))

    # Shorter query to widen coverage.
    if len(terms) >= 3:
        add_query(" ".join(terms[:3]))

    # Search for topic relationships using words
    # already present in the headline.
    detected = detect_topics(title)

    if len(detected) >= 2:
        topic_terms = []

        for topic in detected:
            vocabulary = TOPIC_TERMS[topic]

            matching = [
                word
                for word in terms
                if word.lower() in vocabulary
            ]

            topic_terms.extend(matching[:2])

        add_query(" ".join(topic_terms))

    # Search the last few content words, which
    # may describe the underlying capability.
    if len(terms) >= 4:
        add_query(" ".join(terms[-4:]))

    return queries[:max_queries]


def historical_topic_score(current_title, candidate_title):
    """
    A broad topic-overlap score.

    This is only a retrieval heuristic, not
    proof of historical relevance.
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

    if not overlap:
        return 0.0

    # Reward direct topic overlap.
    direct_score = len(overlap) / len(current_terms)

    # Reward shared technology categories.
    current_topics = set(detect_topics(current_title))
    candidate_topics = set(detect_topics(candidate_title))

    shared_topics = current_topics & candidate_topics

    topic_score = (
        len(shared_topics) / len(current_topics)
        if current_topics
        else 0.0
    )

    return round(
        0.7 * direct_score + 0.3 * topic_score,
        3,
    )
