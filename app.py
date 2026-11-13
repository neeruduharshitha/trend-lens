from pathlib import Path
import streamlit as st
from email.utils import parsedate_to_datetime

from src.collector import fetch_news

def truncate_summary(summary, max_length=180):
    if len(summary) <= max_length:
        return summary

    shortened = summary[:max_length].rsplit(" ", 1)[0]

    return shortened.rstrip(".,;:") + "..."

st.set_page_config(
    page_title="Trend Lens",
    page_icon="🔎",
    layout="wide",
)
css_path = Path(__file__).parent / "styles" / "main.css"

with open(css_path, encoding="utf-8") as css_file:
    st.markdown(
        f"<style>{css_file.read()}</style>",
        unsafe_allow_html=True,
    )
st.title("🔎 Trend Lens")
st.subheader("AI-Powered Technology Intelligence & Engineering Learning")

st.write(
    "Stay updated on important AI and technology developments, "
    "understand their engineering impact, and discover what to learn next."
)

st.info("Welcome to Trend Lens! Your technology intelligence journey starts here.")

st.header("Latest AI & Technology News")

feed_url = "https://techcrunch.com/feed/"
articles = fetch_news(feed_url)

st.write(f"Found {len(articles)} articles.")

for index in range(0, len(articles), 2):
    left_col, right_col = st.columns(2, gap="medium")

    with left_col:
        article = articles[index]

        with st.container(border=True, height="stretch"):
            st.markdown(
                f"#### [{article['title']}]({article['link']})"
            )

            summary = article.get("summary", "")

            if summary:
                st.write(truncate_summary(summary))

            published = article.get("published", "")

            if published:
                try:
                    formatted_date = parsedate_to_datetime(published).strftime("%b %d, %Y")
                except (TypeError, ValueError, IndexError):
                    formatted_date = published

                st.caption(formatted_date)

    if index + 1 < len(articles):
        with right_col:
            article = articles[index + 1]

            with st.container(border=True, height="stretch"):
                st.markdown(
                    f"#### [{article['title']}]({article['link']})"
                )

                summary = article.get("summary", "")

                if summary:
                    st.write(truncate_summary(summary))

                published = article.get("published", "")

                if published:
                    try:
                        formatted_date = parsedate_to_datetime(published).strftime("%b %d, %Y")
                    except (TypeError, ValueError, IndexError):
                        formatted_date = published

                st.caption(formatted_date)