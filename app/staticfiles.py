import os
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

from django.conf import settings
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import StaticFilesStorage


class VersionedStaticFilesStorage(StaticFilesStorage):
    """Append a file mtime query string to static URLs for cache busting."""

    def url(self, name, *args, **kwargs):
        base_url = super().url(name, *args, **kwargs)
        version = getattr(settings, "STATIC_VERSION", None) or self._file_mtime_version(name)
        if not version:
            return base_url

        parts = urlsplit(base_url)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query["v"] = version
        return urlunsplit((
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query),
            parts.fragment,
        ))

    def _file_mtime_version(self, name):
        clean_name = str(name).lstrip("/")

        path = finders.find(clean_name)
        if not path:
            try:
                path = self.path(clean_name)
            except Exception:
                path = None

        if isinstance(path, (list, tuple)):
            path = path[0] if path else None

        if not path or not os.path.exists(path):
            return None

        try:
            return str(int(os.path.getmtime(path)))
        except OSError:
            return None
