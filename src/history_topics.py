
import re


TOPIC_GROUPS = {
    "ai_chips": {
        "ai chip", "ai chips", "nvidia", "blackwell",
        "gpu", "gpus", "semiconductor", "semiconductors",
    },
    "export_restrictions": {
        "export control", "export controls",
        "export ban", "export bans", "chip curbs",
        "chip restrictions", "trade restrictions",
        "banned chips",
    },
    "china": {
        "china", "chinese", "beijing",
    },
    "remote_compute": {
        "remote access", "remote compute",
        "computing remotely", "cloud computing",
        "cloud infrastructure", "data center",
        "data centre", "overseas infrastructure",
    },
    "artificial_intelligence": {
        "artificial intelligence", "ai native",
        "generative ai", "foundation model",
        "large language model", "llm", "llms",
        "ai agent", "ai agents", "machine learning",
    },
    "venture_capital": {
        "venture capital", "venture capitalist",
        "vc firm", "vc fund", "ventures",
        "venture fund", "investment firm",
        "investment fund", "investor",
        "investors", "investing", "investments",
        "backed", "backing",
    },
    "fundraising": {
        "fundraise", "fundraising", "funding",
        "raised", "raises", "raise",
        "million fund", "billion fund",
        "seed round", "series a", "series b",
        "capital raise",
    },
    "startups": {
        "startup", "startups", "early stage",
        "founder", "founders",
    },
    "acquisitions": {
        "acquisition", "acquire", "acquired",
        "acquires", "merger", "merges",
        "takeover", "buyout",
    },
    "cybersecurity": {
        "cybersecurity", "ransomware", "malware",
        "data breach", "security breach",
        "vulnerability", "cyberattack",
    },
    "robotics": {
        "robot", "robots", "robotics",
        "autonomous", "drone", "drones",
    },
    "cloud": {
        "cloud platform", "cloud services",
        "cloud computing", "data center",
        "datacenter", "cloud infrastructure",
    },
}


def normalize_topic_text(text):
    if not isinstance(text, str):
        return ""

    return " ".join(
        re.findall(r"[a-z0-9]+", text.lower())
    )


def extract_topics(text):
    normalized = normalize_topic_text(text)

    if not normalized:
        return set()

    padded = f" {normalized} "

    return {
        topic
        for topic, phrases in TOPIC_GROUPS.items()
        if any(
            f" {normalize_topic_text(phrase)} " in padded
            for phrase in phrases
        )
    }


def topic_relevance(current_title, candidate_title):
    current_topics = extract_topics(current_title)
    candidate_topics = extract_topics(candidate_title)

    if not current_topics or not candidate_topics:
        return 0.0

    shared = current_topics & candidate_topics

    if not shared:
        return 0.0

    return round(
        len(shared) / len(current_topics),
        3,
    )
