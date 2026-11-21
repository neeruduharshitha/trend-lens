
import html
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

import streamlit as st

from src.article_extractor import extract_article
from src.ai_explainer import explain_article
from src.history_ui import render_historical_context


@st.cache_data(ttl=3600, show_spinner=False)
def get_article_content(url):
    """Retrieve and cache the original article text."""
    return extract_article(url)


@st.cache_data(ttl=3600, show_spinner=False)
def get_ai_explanation(title, article_text):
    """Generate and cache a local AI briefing."""
    return explain_article(title, article_text)


def escape(value):
    """Escape text before inserting it into custom HTML."""
    return html.escape(str(value or ""))


def format_article_date(value):
    """Format an RSS publication date."""
    if not value:
        return ""

    try:
        return parsedate_to_datetime(value).strftime(
            "%B %d, %Y"
        )
    except (TypeError, ValueError, IndexError):
        return str(value)


def valid_article_url(url):
    """Return a usable HTTPS article URL."""
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



def section_heading(number, eyebrow, title, description=""):
    """Render an editorial section heading without HTML parsing issues."""

    description_html = (
        f'<p class="tl-section-description">{escape(description)}</p>'
        if description
        else ""
    )

    heading_html = (
        '<div class="tl-section-heading">'
        f'<div class="tl-section-number">{escape(number)}</div>'
        '<div class="tl-section-heading-content">'
        f'<div class="tl-section-eyebrow">{escape(eyebrow)}</div>'
        f'<h2>{escape(title)}</h2>'
        f'{description_html}'
        '</div>'
        '</div>'
    )

    st.markdown(
        heading_html,
        unsafe_allow_html=True,
    )




def render_reading_section(number, eyebrow, title, content):
    """Render a briefing section with clean spacing."""

    if not content:
        return

    section_heading(number, eyebrow, title)

    content_html = (
        '<div class="tl-reading-content">'
        f'{escape(content)}'
        '</div>'
    )

    st.markdown(
        content_html,
        unsafe_allow_html=True,
    )


def render_terms(terms):
    """Display terminology in compact editorial cards."""

    cleaned = [
        item
        for item in terms
        if isinstance(item, dict)
        and str(item.get("term", "")).strip()
        and str(item.get("meaning", "")).strip()
    ][:4]

    if not cleaned:
        return

    section_heading(
        "04",
        "QUICK REFERENCE",
        "Terms to know",
        "A few concepts that make this story easier to understand.",
    )

    for start in range(0, len(cleaned), 2):
        columns = st.columns(2, gap="medium")

        for column, item in zip(
            columns,
            cleaned[start:start + 2],
        ):
            with column:
                st.markdown(
                    f"""
<div class="tl-term-card">
    <div class="tl-term-accent"></div>
    <h3>{escape(item["term"])}</h3>
    <p>{escape(item["meaning"])}</p>
</div>
""",
                    unsafe_allow_html=True,
                )


def render_comparison(comparison):
    """Show the reported before-and-after comparison."""

    if not isinstance(comparison, dict):
        return

    before = str(comparison.get("before") or "").strip()
    after = str(comparison.get("after") or "").strip()
    detail = str(
        comparison.get("explanation") or ""
    ).strip()

    if not before or not after:
        return

    section_heading(
        "05",
        "THE SHIFT",
        "What's different now?",
        "How the announcement changes the picture, "
        "based on the available reporting.",
    )

    left, right = st.columns(2, gap="medium")

    with left:
        st.markdown(
            f"""
<div class="tl-comparison-card tl-comparison-before">
    <div class="tl-comparison-label">BEFORE</div>
    <p>{escape(before)}</p>
</div>
""",
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            f"""
<div class="tl-comparison-card tl-comparison-after">
    <div class="tl-comparison-label">NOW</div>
    <p>{escape(after)}</p>
</div>
""",
            unsafe_allow_html=True,
        )

    if detail:
        st.markdown(
            f"""
<div class="tl-comparison-note">
    {escape(detail)}
</div>
""",
            unsafe_allow_html=True,
        )


def render_open_questions(questions):
    """Display unresolved questions separately from facts."""

    cleaned = [
        str(question).strip()
        for question in questions
        if isinstance(question, str)
        and question.strip()
    ][:3]

    if not cleaned:
        return

    section_heading(
        "06",
        "LOOKING AHEAD",
        "What we still don't know",
        "Questions that remain unanswered in the reporting.",
    )

    for index, question in enumerate(cleaned, start=1):
        st.markdown(
            f"""
<div class="tl-question-row">
    <span class="tl-question-index">{index:02d}</span>
    <span>{escape(question)}</span>
</div>
""",
            unsafe_allow_html=True,
        )


def show_article_detail(article):
    """Display the article and its AI-generated briefing."""

    article_key = (
        article.get("link")
        or article.get("title")
        or "article"
    )

    if "ai_explanations" not in st.session_state:
        st.session_state.ai_explanations = {}

    explanation = st.session_state.ai_explanations.get(
        article_key
    )

    title = str(article.get("title") or "Untitled article")
    source = str(article.get("source") or "Tech news")
    published = format_article_date(
        article.get("published")
    )
    article_url = valid_article_url(
        article.get("link")
    )

    # -----------------------------------------------------
    # Article header
    # -----------------------------------------------------

    st.markdown(
        """
<div class="tl-article-kicker">
    <span class="tl-kicker-dot"></span>
    THE DEEP DIVE
    <span class="tl-kicker-separator">/</span>
    TREND LENS
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class="tl-article-header">
    <h1>{escape(title)}</h1>
    <div class="tl-article-meta">
        <span>{escape(source)}</span>
        <span class="tl-meta-divider"></span>
        <span>{escape(published)}</span>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    if article_url:
        st.link_button(
            "Read original reporting ↗",
            article_url,
        )

    st.markdown(
        '<div class="tl-editorial-rule"></div>',
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # Preview before generation
    # -----------------------------------------------------

    if explanation is None:
        st.markdown(
            '<div class="tl-eyebrow">THE STORY AT A GLANCE</div>',
            unsafe_allow_html=True,
        )

        st.write(
            article.get("summary")
            or "A summary is not available for this article."
        )

        st.write("")

    # -----------------------------------------------------
    # Generate or regenerate AI briefing
    # -----------------------------------------------------

    button_label = (
        "↻ Regenerate briefing"
        if explanation is not None
        else "✦ Generate AI briefing"
    )

    if st.button(
        button_label,
        key=f"generate_{article_key}",
        type=(
            "primary"
            if explanation is None
            else "secondary"
        ),
    ):
        if not article_url:
            st.warning(
                "This article has no valid HTTPS source URL."
            )
        else:
            with st.spinner(
                "Reading the original article..."
            ):
                full_text = get_article_content(
                    article_url
                )

            if not full_text:
                st.warning(
                    "The full article could not be retrieved. "
                    "Please use the original article link."
                )
            else:
                with st.spinner(
                    "Preparing your AI briefing..."
                ):
                    if explanation is not None:
                        get_ai_explanation.clear()

                    new_explanation = get_ai_explanation(
                        title,
                        full_text,
                    )

                if new_explanation:
                    st.session_state.ai_explanations[
                        article_key
                    ] = new_explanation

                    st.rerun()
                else:
                    st.error(
                        "Unable to generate the briefing. "
                        "Check that Ollama is running "
                        "and try again."
                    )

    if explanation is None:
        return

    # -----------------------------------------------------
    # Briefing introduction
    # -----------------------------------------------------

    st.markdown(
        """
<div class="tl-briefing-banner">
    <div class="tl-briefing-icon">✦</div>
    <div>
        <div class="tl-briefing-eyebrow">
            AI-POWERED ANALYSIS
        </div>
        <div class="tl-briefing-title">
            The Briefing
        </div>
        <div class="tl-briefing-subtitle">
            A clearer look at what happened,
            why it matters, and what comes next.
        </div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # 01 — What happened
    # -----------------------------------------------------

    render_reading_section(
        "01",
        "THE UPDATE",
        "What happened",
        explanation.get("what_happened", ""),
    )

    # -----------------------------------------------------
    # 02 — Why it matters
    # -----------------------------------------------------

    render_reading_section(
        "02",
        "THE SIGNIFICANCE",
        "Why it matters",
        explanation.get("why_it_matters", ""),
    )

    # -----------------------------------------------------
    # 03 — Before the News
    # -----------------------------------------------------

    st.markdown(
        """
<div class="tl-history-intro">
    <div class="tl-history-intro-label">
        03 / THE BACKSTORY
    </div>
    <div class="tl-history-intro-text">
        Every announcement has a history.
        Explore earlier reporting behind this story.
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    render_historical_context(article)

    # -----------------------------------------------------
    # 04 — Terms to know
    # -----------------------------------------------------

    render_terms(
        explanation.get("terms_to_know", [])
    )

    # -----------------------------------------------------
    # 05 — What's different now?
    # -----------------------------------------------------

    render_comparison(
        explanation.get("whats_different_now", {})
    )

    # -----------------------------------------------------
    # 06 — Open questions
    # -----------------------------------------------------

    render_open_questions(
        explanation.get("open_questions", [])
    )

    # -----------------------------------------------------
    # AI transparency footer
    # -----------------------------------------------------

    st.markdown(
        """
<div class="tl-ai-disclaimer">
    <span class="tl-disclaimer-icon">ⓘ</span>
    <span>
        This briefing was generated locally using AI
        from the retrieved article. It has not been
        independently verified. Historical context
        links to earlier publisher reporting.
    </span>
</div>
""",
        unsafe_allow_html=True,
    )
