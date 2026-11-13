
import trafilatura


def extract_article(url):
    """Retrieve the readable text of a news article."""

    if not url:
        return None

    try:
        downloaded = trafilatura.fetch_url(url)

        if not downloaded:
            return None

        article_text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
        )

        return article_text or None

    except Exception:
        return None
