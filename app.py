
from pathlib import Path
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta, timezone
import logging

import streamlit as st

from src.collector import fetch_news
from src.article_detail import show_article_detail
from src.news_storage import save_articles, get_articles_for_day


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

logger = logging.getLogger(__name__)


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

        st.markdown(
            f"#### [{article['title']}]({article['link']})"
        )

        summary = article.get("summary", "")

        if summary:
            st.write(truncate_summary(summary))

        published = format_date(
            article.get("published", "")
        )

        if published:
            st.caption(published)

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
# 7. FETCH AND SAVE NEWS
# =========================================================

feed_url = "https://techcrunch.com/feed/"

try:
    live_articles = fetch_news(feed_url)

    # Save articles each time the feed is successfully fetched.
    # Duplicate URLs update existing rows rather than adding copies.
    save_articles(live_articles)

except Exception:
    logger.exception("News collection or storage failed")
    live_articles = []
    st.warning(
        "The latest news could not be refreshed. "
        "You can still browse previously saved articles."
    )


# =========================================================
# 8. SEVEN-DAY NEWS ARCHIVE
# =========================================================

st.header("Explore the Past Seven Days")

today = datetime.now(timezone.utc).date()

available_days = [
    today - timedelta(days=offset)
    for offset in range(7)
]

day_labels = {
    day.strftime("%a, %b %d"): day
    for day in available_days
}

selected_label = st.selectbox(
    "Select a publication date",
    options=list(day_labels.keys()),
    index=0,
)

selected_day = day_labels[selected_label]

st.caption(
    "Articles are grouped by publication date in UTC. "
    "The archive includes articles collected by Trend Lens."
)


# =========================================================
# 9. LOAD SAVED ARTICLES
# =========================================================

try:
    articles = get_articles_for_day(selected_day)
except Exception:
    logger.exception("Unable to read saved articles")
    articles = []
    st.error("The news archive could not be loaded.")

st.header(
    f"News from {selected_day.strftime('%B %d, %Y')}"
)

st.write(f"Found {len(articles)} saved articles.")

if not articles:
    st.info(
        "No articles have been collected for this date yet. "
        "Older dates will populate as Trend Lens saves news "
        "from its RSS sources."
    )


# =========================================================
# 10. TWO-COLUMN NEWS GRID
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
