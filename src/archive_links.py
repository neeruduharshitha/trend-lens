
"""Validate publisher URLs for the Trend Lens news archive."""

import ipaddress
from urllib.parse import urlsplit


BLOCKED_HOSTS = {
    "localhost",
    "news.google.com",
}


def valid_archive_url(url):
    """Check whether a URL is suitable for archive storage."""

    if not isinstance(url, str):
        return False

    try:
        parsed = urlsplit(url.strip())
        hostname = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except ValueError:
        return False

    if parsed.scheme != "https":
        return False

    if not hostname:
        return False

    if parsed.username or parsed.password:
        return False

    if port not in (None, 443):
        return False

    if hostname in BLOCKED_HOSTS:
        return False

    if hostname.endswith((".localhost", ".local")):
        return False

    try:
        ipaddress.ip_address(hostname)
        return False
    except ValueError:
        pass

    if "." not in hostname:
        return False

    return True
