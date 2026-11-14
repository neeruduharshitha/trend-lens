
import ipaddress
import socket
from urllib.parse import urlsplit

import requests
import trafilatura


# Maximum HTML response size: 2 MB
MAX_HTML_BYTES = 2_000_000

# Maximum extracted article length
MAX_ARTICLE_CHARS = 12_000

# Approved publishers for the initial prototype
ALLOWED_PUBLISHERS = {
    "techcrunch.com",
    "reuters.com",
    "theverge.com",
    "arstechnica.com",
    "wired.com",
    "cnbc.com",
    "fortune.com",
}


def publisher_host(url):
    """
    Validate a publisher URL.

    Only HTTPS URLs belonging to approved publishers
    are accepted.

    Returns the hostname or None.
    """

    if not isinstance(url, str):
        return None

    try:
        parsed = urlsplit(url.strip())
        hostname = (parsed.hostname or "").lower()
        port = parsed.port

    except ValueError:
        return None

    if parsed.scheme != "https":
        return None

    if parsed.username or parsed.password:
        return None

    if port not in (None, 443):
        return None

    if not hostname:
        return None

    for domain in ALLOWED_PUBLISHERS:
        if (
            hostname == domain
            or hostname.endswith("." + domain)
        ):
            return hostname

    return None


def has_public_dns(hostname):
    """
    Check that the publisher hostname resolves
    only to publicly routable IP addresses.

    This is a defense-in-depth check, not a
    complete protection against DNS rebinding.
    """

    try:
        addresses = socket.getaddrinfo(
            hostname,
            443,
            type=socket.SOCK_STREAM,
        )

    except (socket.gaierror, OSError):
        return False

    if not addresses:
        return False

    for address in addresses:
        ip_text = address[4][0]

        try:
            ip = ipaddress.ip_address(ip_text)

        except ValueError:
            return False

        if not ip.is_global:
            return False

    return True


def extract_publisher_article(
    publisher_url,
    timeout=15,
):
    """
    Download and extract article text from an
    approved publisher.

    Returns:
        str: Extracted article text.
        None: If validation, download, or
              extraction fails.

    Restrictions:
    - HTTPS only
    - Approved publishers only
    - No automatic redirects
    - No JavaScript execution
    - No paywall bypass
    - Maximum HTML size enforced
    """

    # Step 1: Validate the publisher URL
    hostname = publisher_host(publisher_url)

    if hostname is None:
        return None

    # Step 2: Validate DNS resolution
    if not has_public_dns(hostname):
        return None

    try:
        # Step 3: Create an HTTP session
        with requests.Session() as session:

            # Ignore environment proxy settings
            session.trust_env = False

            # Step 4: Request publisher article
            with session.get(
                publisher_url,
                headers={
                    "User-Agent": "TrendLens/0.1",
                    "Accept": "text/html",
                },
                timeout=(5, timeout),
                allow_redirects=False,
                stream=True,
            ) as response:

                # Require successful response
                if response.status_code != 200:
                    return None

                # Require HTML content
                content_type = response.headers.get(
                    "Content-Type", ""
                ).lower()

                if "text/html" not in content_type:
                    return None

                # Check declared response size
                content_length = response.headers.get(
                    "Content-Length"
                )

                if content_length:
                    try:
                        if int(content_length) > MAX_HTML_BYTES:
                            return None

                    except ValueError:
                        return None

                # Step 5: Read response in chunks
                chunks = []
                total = 0

                for chunk in response.iter_content(
                    chunk_size=16384
                ):
                    total += len(chunk)

                    if total > MAX_HTML_BYTES:
                        return None

                    chunks.append(chunk)

        # Step 6: Decode HTML
        html = b"".join(chunks).decode(
            "utf-8",
            errors="replace",
        )

        # Step 7: Extract main article text
        text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
        )

        if not text:
            return None

        # Step 8: Normalize whitespace
        text = " ".join(text.split())

        # Reject articles with insufficient content
        if len(text) < 150:
            return None

        # Step 9: Return extracted article text
        return text[:MAX_ARTICLE_CHARS]

    except (
        requests.RequestException,
        OSError,
    ):
        return None
