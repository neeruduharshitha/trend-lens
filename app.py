
from pathlib import Path
from email.utils import parsedate_to_datetime

import streamlit as st
import logging

from src.collector import fetch_news
from src.article_detail import show_article_detail


# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Trend Lens",
    page_icon="🔎",
    layout="wide",
)


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(name)s | %(message)s",
)


# =========================================================
# 2. LOAD DESIGN SYSTEM
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
CSS_PATH = BASE_DIR / "styles" / "main.css"

if CSS_PATH.is_file():
    css = CSS_PATH.read_text(encoding="utf-8")

    st.markdown(
        f"<style>\n{css}\n</style>",
        unsafe_allow_html=True,
    )
else:
    st.error(
        f"Trend Lens stylesheet could not be found: {CSS_PATH}"
    )


# =========================================================
# 3. HELPER FUNCTIONS
# =========================================================

def truncate_summary(summary, max_length=180):
    """Shorten summaries without cutting words in half."""

    summary = str(summary or "")

    if len(summary) <= max_length:
        return summary

    shortened = summary[:max_length].rsplit(" ", 1)[0]

    return shortened.rstrip(".,;:") + "..."


def format_date(published):
    """Convert RSS publication dates to a readable format."""

    if not published:
        return ""

    try:
        return parsedate_to_datetime(published).strftime(
            "%b %d, %Y"
        )
    except (TypeError, ValueError, IndexError):
        return str(published)


def display_article_card(article, index):
    """Display an article in the Trend Lens news grid."""

    with st.container(border=True, height="stretch"):

        # Article headline
        st.markdown(
            f"#### [{article['title']}]({article['link']})"
        )

        # Short article summary
        summary = article.get("summary", "")

        if summary:
            st.write(
                truncate_summary(summary)
            )

        # Publication date
        published = format_date(
            article.get("published", "")
        )

        if published:
            st.caption(published)

        # Open the internal article detail page
        if st.button(
            "Understand this news →",
            key=f"article_{index}",
        ):
            st.session_state.selected_article = article
            st.rerun()


# =========================================================
# 4. SESSION STATE
# =========================================================

if "selected_article" not in st.session_state:
    st.session_state.selected_article = None


# =========================================================
# 5. ARTICLE DETAIL VIEW
# =========================================================

if st.session_state.selected_article is not None:

    if st.button("← Back to news"):
        st.session_state.selected_article = None
        st.rerun()

    show_article_detail(
        st.session_state.selected_article
    )

    st.stop()


# =========================================================
# 6. HOMEPAGE
# =========================================================

st.title("🔎 Trend Lens")

st.subheader(
    "AI-Powered Technology Intelligence & Engineering Learning"
)

st.write(
    "Stay updated on important AI and technology developments, "
    "understand their engineering impact, "
    "and discover what to learn next."
)

st.info(
    "Welcome to Trend Lens! "
    "Your technology intelligence journey starts here."
)


# =========================================================
# 7. LIVE NEWS FEED
# =========================================================

st.header("Latest AI & Technology News")

feed_url = "https://techcrunch.com/feed/"

articles = fetch_news(feed_url)

st.write(
    f"Found {len(articles)} articles."
)


# =========================================================
# 8. TWO-COLUMN NEWS GRID
# =========================================================

for index in range(0, len(articles), 2):

    left_col, right_col = st.columns(
        2,
        gap="medium",
    )

    with left_col:
        display_article_card(
            articles[index],
            index,
        )

    if index + 1 < len(articles):
        with right_col:
            display_article_card(
                articles[index + 1],
                index + 1,
            )
