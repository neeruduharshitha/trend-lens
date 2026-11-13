
from pathlib import Path
from email.utils import parsedate_to_datetime

import streamlit as st

from src.collector import fetch_news
from src.article_detail import show_article_detail


# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def truncate_summary(summary, max_length=180):
    """Shorten article summaries without cutting words in half."""
    if len(summary) <= max_length:
        return summary

    shortened = summary[:max_length].rsplit(" ", 1)[0]

    return shortened.rstrip(".,;:") + "..."


def format_date(published):
    """Convert RSS publication dates into a readable format."""
    if not published:
        return ""

    try:
        return parsedate_to_datetime(published).strftime("%b %d, %Y")
    except (TypeError, ValueError, IndexError):
        return published


def display_article_card(article, index):
    """Display a single editorial news postcard."""

    with st.container(border=True, height="stretch"):

        # Clickable headline opens the original article
        st.markdown(
            f"#### [{article['title']}]({article['link']})"
        )

        # Short article preview
        summary = article.get("summary", "")

        if summary:
            st.write(truncate_summary(summary))

        # Publication date
        formatted_date = format_date(article.get("published", ""))

        if formatted_date:
            st.caption(formatted_date)

        # Open the article detail view inside Trend Lens
        if st.button(
            "Understand this news →",
            key=f"article_{index}",
        ):
            st.session_state.selected_article = article
            st.rerun()


# --------------------------------------------------
# Streamlit page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Trend Lens",
    page_icon="🔎",
    layout="wide",
)


# --------------------------------------------------
# Session state
# --------------------------------------------------

if "selected_article" not in st.session_state:
    st.session_state.selected_article = None


# --------------------------------------------------
# Load custom CSS
# --------------------------------------------------

css_path = Path(__file__).parent / "styles" / "main.css"

with open(css_path, encoding="utf-8") as css_file:
    st.markdown(
        f"<style>{css_file.read()}</style>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# Article detail view
# --------------------------------------------------

if st.session_state.selected_article is not None:

    if st.button("← Back to news"):
        st.session_state.selected_article = None
        st.rerun()

    show_article_detail(st.session_state.selected_article)

    st.stop()


# --------------------------------------------------
# Homepage
# --------------------------------------------------

st.title("🔎 Trend Lens")

st.subheader(
    "AI-Powered Technology Intelligence & Engineering Learning"
)

st.write(
    "Stay updated on important AI and technology developments, "
    "understand their engineering impact, and discover what to learn next."
)

st.info(
    "Welcome to Trend Lens! Your technology intelligence journey starts here."
)


# --------------------------------------------------
# Live news feed
# --------------------------------------------------

st.header("Latest AI & Technology News")

feed_url = "https://techcrunch.com/feed/"

articles = fetch_news(feed_url)

st.write(f"Found {len(articles)} articles.")


# --------------------------------------------------
# Two-column editorial postcard grid
# --------------------------------------------------

for index in range(0, len(articles), 2):

    left_col, right_col = st.columns(2, gap="medium")

    with left_col:
        display_article_card(articles[index], index)

    if index + 1 < len(articles):
        with right_col:
            display_article_card(articles[index + 1], index + 1)
