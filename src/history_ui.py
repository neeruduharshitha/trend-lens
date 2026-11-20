
import html
import re
from datetime import date
from urllib.parse import urlsplit

import streamlit as st

from src.history_pipeline import build_historical_evidence
from src.history_timeline import generate_historical_timeline


# =========================================================
# 1. Historical context retrieval
# =========================================================

@st.cache_data(ttl=3600, show_spinner=False)
def get_historical_timeline(title, link, published):
    """Retrieve and generate historical context for one article."""

    article = {
        "title": title,
        "link": link,
        "published": published,
    }

    evidence = build_historical_evidence(
        article,
        max_search_results=30,
        max_resolve_results=20,
        limit=5,
        min_age_days=7,
    )

    if not evidence:
        return []

    return generate_historical_timeline(
        article,
        evidence,
        model="qwen2.5:3b",
    )


# =========================================================
# 2. Formatting helpers
# =========================================================

def format_timeline_date(value):
    """Convert an ISO date into a readable editorial date."""

    try:
        return date.fromisoformat(value).strftime("%b %d, %Y")
    except (TypeError, ValueError):
        return str(value or "")


def clean_headline(title, source):
    """Remove a redundant publisher suffix from a headline."""

    title = str(title or "").strip()
    source = str(source or "").strip()

    if not source:
        return title

    return re.sub(
        rf"\s*[-–—|]\s*{re.escape(source)}\s*$",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()


def safe_source_url(url):
    """Allow only valid HTTPS links to publisher articles."""

    if not isinstance(url, str):
        return ""

    url = url.strip()

    try:
        parsed = urlsplit(url)

        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port is not None
        ):
            return ""

    except ValueError:
        return ""

    return url


# =========================================================
# 3. Editorial historical timeline
# =========================================================

def render_timeline_entries(entries):
    """Render verified historical entries as an editorial timeline."""

    if not entries:
        st.info(
            "No verified historical context is available "
            "for this article yet."
        )
        return

    st.caption(
        "A look at earlier reporting that helps explain "
        "the bigger picture."
    )

    items = sorted(
        entries,
        key=lambda item: item["date"],
    )

    for index, entry in enumerate(items):

        title = clean_headline(
            entry.get("title"),
            entry.get("source"),
        )

        date_text = format_timeline_date(
            entry.get("date")
        )

        source = str(
            entry.get("source") or "Original reporting"
        )

        description = str(
            entry.get("description") or ""
        )

        url = safe_source_url(
            entry.get("url")
        )

        relationship = entry.get(
            "relationship",
            "broader_industry_context",
        )

        if relationship == "direct_predecessor":
            relationship_label = "Direct predecessor"
        else:
            relationship_label = "Broader industry context"

        if url:
            link_html = (
                '<a class="tl-history-link" '
                f'href="{html.escape(url, quote=True)}" '
                'target="_blank" '
                'rel="noopener noreferrer">'
                'Read original reporting ↗'
                '</a>'
            )
        else:
            link_html = ""

        st.markdown(
            f"""
<div class="tl-history-item"
     style="animation-delay: {index * 90}ms;">

    <div class="tl-history-marker"></div>

    <div class="tl-history-meta">
        <span>{html.escape(date_text)}</span>
        <span class="tl-history-dot">·</span>
        <span>{html.escape(source)}</span>
    </div>

    <h3>{html.escape(title)}</h3>

    <p>{html.escape(description)}</p>

    <div class="tl-history-footer">
        <span class="tl-history-category">
            {html.escape(relationship_label)}
        </span>

        {link_html}
    </div>

</div>
""",
            unsafe_allow_html=True,
        )


# =========================================================
# 4. Historical context section
# =========================================================

def render_historical_context(article):
    """Show the historical timeline only when requested."""

    st.subheader("Before the News")

    st.caption(
        "Explore earlier developments related to this story, "
        "with links to the original reporting."
    )

    title = article.get("title", "")
    link = article.get("link", "")
    published = article.get("published", "")

    if not all((title, link, published)):
        st.caption(
            "Historical context is unavailable because "
            "this article is missing required information."
        )
        return

    article_key = link

    # Initialize session state.
    if "historical_timelines" not in st.session_state:
        st.session_state.historical_timelines = {}

    if "historical_timeline_attempted" not in st.session_state:
        st.session_state.historical_timeline_attempted = set()

    attempted = st.session_state.historical_timeline_attempted
    timelines = st.session_state.historical_timelines

    # -----------------------------------------------------
    # First visit: offer historical context generation
    # -----------------------------------------------------

    if article_key not in attempted:

        if st.button(
            "Explore historical context",
            key=f"history_{article_key}",
        ):

            with st.spinner(
                "Finding earlier reporting..."
            ):

                try:
                    timeline = get_historical_timeline(
                        title,
                        link,
                        published,
                    )

                except Exception:
                    # External retrieval errors should not
                    # interrupt the main article briefing.
                    st.error(
                        "Historical context could not be retrieved. "
                        "Please try again."
                    )
                    return

            timelines[article_key] = timeline
            attempted.add(article_key)

            st.rerun()

        return

    # -----------------------------------------------------
    # Display previously generated historical context
    # -----------------------------------------------------

    entries = timelines.get(
        article_key,
        [],
    )

    render_timeline_entries(entries)

    # -----------------------------------------------------
    # Refresh historical context
    # -----------------------------------------------------

    if st.button(
        "Refresh historical context",
        key=f"refresh_history_{article_key}",
    ):

        attempted.discard(article_key)
        timelines.pop(article_key, None)

        # Clear cached retrieval results so a new
        # search can be performed.
        get_historical_timeline.clear()

        st.rerun()
