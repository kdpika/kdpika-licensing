"""TLS-only, bounded transport. Only public-key GET is eligible for retry."""

from __future__ import annotations

import math
import random
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any, Protocol, cast
from urllib.parse import urlsplit

from ._json import MAX_BYTES, canonical
from ._version import __version__
from .errors import ConfigurationError, NetworkError
from .models import HttpResponse


class Transport(Protocol):
    def request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> HttpResponse: ...


def safe_url(value: str, allow_loopback_http: bool = False) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
        port = parsed.port
        if port is not None and not 0 < port < 65536:
            return False
        if value != value.strip() or any(ord(c) < 33 for c in value) or "\\" in value:
            return False
        if (
            parsed.username
            or parsed.password
            or not parsed.hostname
            or parsed.query
            or parsed.fragment
            or parsed.path not in ("", "/")
        ):
            return False
        return parsed.scheme == "https" or (
            allow_loopback_http
            and parsed.scheme == "http"
            and parsed.hostname in {"127.0.0.1", "::1", "localhost"}
        )
    except ValueError:
        return False


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


class HttpTransport:
    def __init__(
        self,
        base_url: str,
        timeout: float = 15.0,
        user_agent: str | None = None,
        *,
        allow_loopback_http: bool = False,
    ) -> None:
        if (
            not safe_url(base_url, allow_loopback_http)
            or not isinstance(timeout, (int, float))
            or isinstance(timeout, bool)
            or not math.isfinite(timeout)
            or not 0 < timeout <= 120
        ):
            raise ConfigurationError()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.user_agent = user_agent or "KDPika-Licensing-Python/" + __version__
        # Default HTTPS handler validates certificates; no configurable bypass.
        self._opener = urllib.request.build_opener(_NoRedirect())

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> HttpResponse:
        if (
            method not in {"GET", "POST"}
            or not path.startswith("/api/v1/")
            or any(c in path for c in "?#\r\n")
        ):
            raise ConfigurationError()
        request_headers = {"Accept": "application/json", "User-Agent": self.user_agent}
        request_headers.update(headers or {})
        data = None if body is None else canonical(body)
        if data is not None:
            request_headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            self.base_url + path, data=data, headers=request_headers, method=method
        )
        retries = 1 if method == "GET" and path == "/api/v1/public-key" else 0
        for attempt in range(retries + 1):
            try:
                response = self._once(request)
            except NetworkError:
                if attempt == retries:
                    raise
                time.sleep(random.uniform(0.1, 0.3))
                continue
            if attempt < retries and response.status in {429, 502, 503, 504}:
                delay = self._retry_after(response.headers)
                # Do not retry before a long server cooldown or block the GUI for it.
                if delay is None:
                    return response
                time.sleep(max(delay, random.uniform(0.1, 0.3)))
                continue
            return response
        raise NetworkError()  # Defensive bound, no indefinite retry loop.

    def _once(self, request: urllib.request.Request) -> HttpResponse:
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                return self._read(response)
        except urllib.error.HTTPError as error:
            with error:
                return self._read(error)
        except (urllib.error.URLError, TimeoutError, OSError):
            raise NetworkError() from None

    @staticmethod
    def _read(response: Any) -> HttpResponse:
        raw = cast(bytes, response.read(MAX_BYTES + 1))
        return HttpResponse.from_bytes(int(response.code), dict(response.headers.items()), raw)

    @staticmethod
    def _retry_after(headers: dict[str, str]) -> float | None:
        raw = next((v for k, v in headers.items() if k.lower() == "retry-after"), None)
        if raw is None:
            return 0.0
        try:
            value = float(raw)
        except ValueError:
            try:
                date = parsedate_to_datetime(raw)
                value = (date - datetime.now(UTC)).total_seconds()
            except (ValueError, TypeError, OverflowError):
                return None
        return max(0.0, value) if math.isfinite(value) and value <= 2 else None
