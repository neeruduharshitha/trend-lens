
from email.utils import parsedate_to_datetime

import streamlit as st

from src.article_extractor import extract_article
from src.ai_explainer import explain_article


@st.cache_data(ttl=3600, show_spinner=False)
def get_article_content(url):
    """Retrieve and cache article text."""
    return extract_article(url)


@st.cache_data(ttl=3600, show_spinner=False)
def get_ai_explanation(title, article_text):
    """Generate and cache a local AI briefing."""
    return explain_article(title, article_text)


def show_article_detail(article):
    """Display a news preview or a complete AI briefing."""

    article_key = article.get("link") or article["title"]

    if "ai_explanations" not in st.session_state:
        st.session_state.ai_explanations = {}

    explanation = st.session_state.ai_explanations.get(article_key)

    # -------------------------------------------
    # Article header
    # -------------------------------------------

    st.caption("TREND LENS / ARTICLE")
    st.title(article["title"])

    if article.get("published"):
        published = article["published"]

        try:
            published = parsedate_to_datetime(published).strftime(
                "%b %d, %Y"
            )
        except (TypeError, ValueError, IndexError):
            pass

        st.caption(published)

    if article.get("link"):
        st.link_button(
            "Read original article ↗",
            article["link"],
        )

    st.divider()

    # -------------------------------------------
    # Preview: shown before generation
    # -------------------------------------------

    if explanation is None:
        st.caption("THE STORY")

        st.write(
            article.get("summary")
            or "A summary is not available for this article."
        )

        st.write("")

    # -------------------------------------------
    # Generate or regenerate
    # -------------------------------------------

    button_label = (
        "↻ Regenerate briefing"
        if explanation is not None
        else "✦ Generate AI briefing"
    )

    if st.button(
        button_label,
        key=f"generate_{article_key}",
        type="primary" if explanation is None else "secondary",
    ):
        article_url = article.get("link")

        if not article_url:
            st.warning("This article has no source URL.")

        else:
            with st.spinner("Reading the original article..."):
                full_text = get_article_content(article_url)

            if not full_text:
                st.warning(
                    "The full article could not be retrieved. "
                    "Please use the original article link."
                )

            else:
                with st.spinner("Preparing your AI briefing..."):
                    # Force a new generation only when
                    # the user explicitly regenerates.
                    if explanation is not None:
                        get_ai_explanation.clear()

                    new_explanation = get_ai_explanation(
                        article["title"],
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
                        "Check that Ollama is running and try again."
                    )

    # Do not show empty sections before generation
    if explanation is None:
        return

    # -------------------------------------------
    # Full AI briefing
    # -------------------------------------------

    st.caption("AI-GENERATED BRIEFING")

    # 01 — What happened
    st.subheader("What happened")
    st.write(explanation["what_happened"])

    # 02 — Why it matters
    st.subheader("Why it matters")
    st.write(explanation["why_it_matters"])

    # 03 — Terms to know
    terms = [
        item
        for item in explanation.get("terms_to_know", [])
        if item.get("term", "").strip()
        and item.get("meaning", "").strip()
    ][:4]

    if terms:
        st.subheader("Terms to know")

        for start in range(0, len(terms), 2):
            columns = st.columns(2, gap="medium")

            for column, term in zip(
                columns,
                terms[start:start + 2],
            ):
                with column:
                    with st.container(border=True):
                        st.markdown(f"**{term['term']}**")
                        st.write(term["meaning"])

    # 04 — What's different now?
    comparison = explanation.get(
        "whats_different_now", {}
    )

    before = comparison.get("before", "").strip()
    after = comparison.get("after", "").strip()

    if before and after:
        st.subheader("What's different now?")

        left, right = st.columns(2, gap="medium")

        with left:
            with st.container(border=True):
                st.caption("BEFORE")
                st.write(before)

        with right:
            with st.container(border=True):
                st.caption("AFTER")
                st.write(after)

        detail = comparison.get("explanation", "").strip()

        if detail:
            st.write(detail)

    # 05 — What we still don't know
    questions = [
        question.strip()
        for question in explanation.get("open_questions", [])
        if question.strip()
    ][:3]

    if questions:
        st.subheader("What we still don't know")

        for question in questions:
            st.markdown(f"- {question}")

        st.caption(
            "Questions for further reporting, not confirmed facts."
        )

    st.divider()
    st.caption(
        "This briefing was generated locally by AI from the "
        "retrieved article. It has not been independently verified."
    )
