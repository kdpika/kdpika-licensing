"""HTTP security and retry policy with a mocked urllib opener only."""

import io
import urllib.error
from datetime import UTC, datetime, timedelta
from email.message import Message
from email.utils import format_datetime
from unittest.mock import Mock

import pytest

from kdpika_licensing._transport import HttpTransport, _NoRedirect, safe_url
from kdpika_licensing._version import __version__
from kdpika_licensing.errors import ConfigurationError, NetworkError
from kdpika_licensing.models import HttpResponse


class Response(io.BytesIO):
    def __init__(self, raw=b'{"success":true}', code=200, headers=None):
        super().__init__(raw)
        self.code = code
        self.headers = headers or {}


def test_valid_transport_headers_timeout_and_no_redirect(monkeypatch):
    transport = HttpTransport("https://example.invalid")
    opener = Mock()
    opener.open.return_value = Response()
    monkeypatch.setattr(transport, "_opener", opener)
    assert transport.request(
        "POST", "/api/v1/licenses/validate", {}, {"Authorization": "Bearer synthetic"}
    ).ok
    request = opener.open.call_args.args[0]
    assert request.get_header("User-agent") == "KDPika-Licensing-Python/" + __version__
    assert request.get_header("Authorization") == "Bearer synthetic"
    assert opener.open.call_args.kwargs["timeout"] == 15
    assert _NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.invalid") is None


@pytest.mark.parametrize(
    "raw", [b"[]", b"not json", b'{"success":true,"success":false}', b"x" * 1048577, b'"\xff"']
)
def test_invalid_body_is_authoritative_not_a_network_failure(monkeypatch, raw):
    transport = HttpTransport("https://example.invalid")
    transport._opener = Mock()
    transport._opener.open.return_value = Response(raw)
    result = transport.request("POST", "/api/v1/licenses/validate")
    assert not result.ok and result.body["error"]["code"] == "INVALID_RESPONSE"


@pytest.mark.parametrize(
    "error", [urllib.error.URLError("untrusted"), TimeoutError("untrusted"), OSError("untrusted")]
)
def test_no_post_retries_and_safe_errors(monkeypatch, error):
    transport = HttpTransport("https://example.invalid")
    transport._opener = Mock()
    transport._opener.open.side_effect = error
    with pytest.raises(NetworkError) as caught:
        transport.request("POST", "/api/v1/licenses/activate")
    assert "untrusted" not in str(caught.value) and transport._opener.open.call_count == 1


@pytest.mark.parametrize("status", [302, 403, 429, 500])
def test_http_error_stays_response_and_is_not_retried_for_mutations(status):
    transport = HttpTransport("https://example.invalid")
    transport._opener = Mock()
    transport._opener.open.side_effect = urllib.error.HTTPError(
        "https://example.invalid", status, "private", Message(), Response(b'{"success":false}')
    )
    assert transport.request("POST", "/api/v1/licenses/validate").status == status
    assert transport._opener.open.call_count == 1


def test_public_key_get_retry_network_then_success(monkeypatch):
    sleep = Mock()
    monkeypatch.setattr("kdpika_licensing._transport.time.sleep", sleep)
    transport = HttpTransport("https://example.invalid")
    transport._opener = Mock()
    transport._opener.open.side_effect = [TimeoutError(), Response()]
    assert transport.request("GET", "/api/v1/public-key").ok
    assert sleep.call_count == 1 and 0.1 <= sleep.call_args.args[0] <= 0.3


def test_public_key_retry_after_not_before_server_window(monkeypatch):
    sleep = Mock()
    monkeypatch.setattr("kdpika_licensing._transport.time.sleep", sleep)
    transport = HttpTransport("https://example.invalid")
    transport._opener = Mock()
    transport._opener.open.side_effect = [
        Response(b'{"success":false}', 429, {"Retry-After": "1"}),
        Response(),
    ]
    assert transport.request("GET", "/api/v1/public-key").ok and sleep.call_args.args[0] >= 1
    transport._opener.open.side_effect = [Response(b'{"success":false}', 503, {"Retry-After": "60"})]
    sleep.reset_mock()
    assert transport.request("GET", "/api/v1/public-key").status == 503
    assert not sleep.called


@pytest.mark.parametrize(
    "header,expected", [("bad", None), ("nan", None), ("inf", None), ("100", None), ("-1", 0), ("0", 0)]
)
def test_retry_after_malformed_or_long_is_not_ignored(header, expected):
    assert HttpTransport._retry_after({"rEtRy-AfTeR": header}) == expected


def test_retry_after_http_date_and_no_header():
    assert HttpTransport._retry_after({}) == 0
    assert (
        HttpTransport._retry_after({"Retry-After": format_datetime(datetime.now(UTC) - timedelta(seconds=1))})
        == 0
    )
    assert (
        HttpTransport._retry_after({"Retry-After": format_datetime(datetime.now(UTC) + timedelta(minutes=1))})
        is None
    )


@pytest.mark.parametrize(
    "url",
    [
        "https://user:pass@example.invalid",
        "https://example.invalid:99999",
        "https://example.invalid/path",
        "https://example.invalid?secret=1",
        "https://example.invalid#x",
        " https://example.invalid",
        "https://example.invalid\\@evil.invalid",
        "https://example.invalid\n",
        "http://localhost",
        "http://example.invalid",
        "https://[broken",
        "https://",
    ],
)
def test_url_security(url):
    assert not safe_url(url)


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf"), 121])
def test_bounded_timeout(timeout):
    with pytest.raises(ConfigurationError):
        HttpTransport("https://example.invalid", timeout)


@pytest.mark.parametrize(
    "method,path",
    [("DELETE", "/api/v1/x"), ("POST", "//evil.invalid"), ("GET", "/api/v1/x?x=1"), ("POST", "/api/v1/x\n")],
)
def test_invalid_request_route_is_rejected(method, path):
    with pytest.raises(ConfigurationError):
        HttpTransport("https://example.invalid").request(method, path)


def test_get_stops_after_one_retry(monkeypatch):
    monkeypatch.setattr("kdpika_licensing._transport.time.sleep", lambda _: None)
    transport = HttpTransport("https://example.invalid")
    transport._opener = Mock()
    transport._opener.open.side_effect = TimeoutError()
    with pytest.raises(NetworkError):
        transport.request("GET", "/api/v1/public-key")
    assert transport._opener.open.call_count == 2


def test_response_repr_does_not_include_raw_values():
    response = HttpResponse(200, {"Authorization": "PRIVATE"}, {"payload": "PRIVATE"})
    assert "PRIVATE" not in repr(response)
