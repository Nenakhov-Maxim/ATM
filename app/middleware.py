import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.conf import settings


class StaticVersionMiddleware:
    """Ensure every /static/ URL in HTML has the configured static version."""

    def __init__(self, get_response):
        self.get_response = get_response
        static_url = getattr(settings, "STATIC_URL", "/static/")
        if not static_url.startswith("/"):
            static_url = "/" + static_url
        self.static_url = static_url

    def __call__(self, request):
        response = self.get_response(request)

        version = getattr(settings, "STATIC_VERSION", None)
        content_type = response.get("Content-Type", "")
        if (
            not version
            or response.streaming
            or "text/html" not in content_type
            or not getattr(response, "content", None)
        ):
            return response

        charset = getattr(response, "charset", None) or "utf-8"
        html = response.content.decode(charset, errors="ignore")

        pattern = re.compile(
            r'(?P<prefix>\b(?:src|href)=["\'])(?P<url>'
            + re.escape(self.static_url)
            + r'[^"\']+)(?P<suffix>["\'])'
        )
        html = pattern.sub(self._add_version, html)

        response.content = html.encode(charset)
        response["Content-Length"] = str(len(response.content))
        return response

    def _add_version(self, match):
        url = match.group("url")
        parts = urlsplit(url)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        if "v" in query:
            return match.group(0)

        query["v"] = str(settings.STATIC_VERSION)
        versioned_url = urlunsplit((
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query),
            parts.fragment,
        ))
        return f"{match.group('prefix')}{versioned_url}{match.group('suffix')}"
