"""Unit tests for resolve_client_ip and trusted proxy logic."""

from unittest.mock import MagicMock, patch

from app.dependencies import _is_trusted_proxy, resolve_client_ip


class TestIsTrustedProxy:
    def test_single_ip_match(self):
        assert _is_trusted_proxy("10.0.0.1", ["10.0.0.1"]) is True

    def test_single_ip_no_match(self):
        assert _is_trusted_proxy("10.0.0.2", ["10.0.0.1"]) is False

    def test_cidr_match(self):
        assert _is_trusted_proxy("10.0.0.42", ["10.0.0.0/8"]) is True

    def test_cidr_no_match(self):
        assert _is_trusted_proxy("192.168.1.1", ["10.0.0.0/8"]) is False

    def test_multiple_entries(self):
        trusted = ["192.168.1.0/24", "10.0.0.1"]
        assert _is_trusted_proxy("192.168.1.50", trusted) is True
        assert _is_trusted_proxy("10.0.0.1", trusted) is True
        assert _is_trusted_proxy("172.16.0.1", trusted) is False

    def test_invalid_address(self):
        assert _is_trusted_proxy("not-an-ip", ["10.0.0.0/8"]) is False

    def test_invalid_entry_logged(self, caplog):
        assert _is_trusted_proxy("10.0.0.1", ["bad-entry"]) is False
        assert "Invalid trusted proxy entry" in caplog.text

    def test_ipv6(self):
        assert _is_trusted_proxy("::1", ["::1"]) is True
        assert _is_trusted_proxy("::1", ["::2"]) is False


def _make_request(client_host="127.0.0.1", forwarded_for=None):
    """Create a mock Starlette request."""
    request = MagicMock()
    request.client.host = client_host
    request.headers = {}
    if forwarded_for:
        request.headers["x-forwarded-for"] = forwarded_for
    return request


class TestResolveClientIp:
    def test_no_proxies_ignores_forwarded_header(self):
        """With no trusted proxies, X-Forwarded-For is always ignored."""
        request = _make_request(client_host="1.2.3.4", forwarded_for="9.9.9.9")
        with patch("app.dependencies.settings") as mock_settings:
            mock_settings.trusted_proxies_list = []
            assert resolve_client_ip(request) == "1.2.3.4"

    def test_trusted_proxy_uses_forwarded_ip(self):
        """Request from a trusted proxy should use the first X-Forwarded-For IP."""
        request = _make_request(client_host="10.0.0.1", forwarded_for="203.0.113.50, 10.0.0.1")
        with patch("app.dependencies.settings") as mock_settings:
            mock_settings.trusted_proxies_list = ["10.0.0.1"]
            assert resolve_client_ip(request) == "203.0.113.50"

    def test_untrusted_source_ignores_forwarded(self):
        """Request from an untrusted IP should ignore X-Forwarded-For."""
        request = _make_request(client_host="192.168.1.1", forwarded_for="9.9.9.9")
        with patch("app.dependencies.settings") as mock_settings:
            mock_settings.trusted_proxies_list = ["10.0.0.1"]
            assert resolve_client_ip(request) == "192.168.1.1"

    def test_trusted_proxy_no_header_falls_back(self):
        """Trusted proxy with no X-Forwarded-For falls back to direct IP."""
        request = _make_request(client_host="10.0.0.1")
        with patch("app.dependencies.settings") as mock_settings:
            mock_settings.trusted_proxies_list = ["10.0.0.1"]
            assert resolve_client_ip(request) == "10.0.0.1"

    def test_cidr_trusted_proxy(self):
        """CIDR ranges should work for trusted proxy matching."""
        request = _make_request(client_host="172.16.5.10", forwarded_for="8.8.8.8")
        with patch("app.dependencies.settings") as mock_settings:
            mock_settings.trusted_proxies_list = ["172.16.0.0/12"]
            assert resolve_client_ip(request) == "8.8.8.8"

    def test_no_client_returns_unknown(self):
        """Request with no client info returns 'unknown'."""
        request = MagicMock()
        request.client = None
        request.headers = {}
        with patch("app.dependencies.settings") as mock_settings:
            mock_settings.trusted_proxies_list = []
            assert resolve_client_ip(request) == "unknown"
