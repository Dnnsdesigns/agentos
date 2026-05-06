"""Tests for agentos.copilot.auth."""

from __future__ import annotations

import hashlib
import hmac
import unittest
from unittest.mock import MagicMock, patch


class TestVerifySignature(unittest.TestCase):
    """Tests for verify_signature."""

    def setUp(self) -> None:
        from agentos.copilot.auth import verify_signature

        self.verify = verify_signature

    def _make_sig(self, payload: bytes, secret: str) -> str:
        digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return f"sha256={digest}"

    def test_valid_signature(self) -> None:
        payload = b'{"hello": "world"}'
        secret = "mysecret"
        sig = self._make_sig(payload, secret)
        self.assertTrue(self.verify(payload, sig, secret))

    def test_wrong_secret(self) -> None:
        payload = b'{"hello": "world"}'
        sig = self._make_sig(payload, "correct-secret")
        self.assertFalse(self.verify(payload, sig, "wrong-secret"))

    def test_tampered_payload(self) -> None:
        secret = "mysecret"
        sig = self._make_sig(b"original", secret)
        self.assertFalse(self.verify(b"tampered", sig, secret))

    def test_missing_prefix(self) -> None:
        payload = b"data"
        secret = "mysecret"
        raw_hex = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        # Header without "sha256=" prefix
        self.assertFalse(self.verify(payload, raw_hex, secret))

    def test_empty_sig_header(self) -> None:
        self.assertFalse(self.verify(b"data", "", "secret"))

    def test_empty_payload(self) -> None:
        secret = "s"
        sig = self._make_sig(b"", secret)
        self.assertTrue(self.verify(b"", sig, secret))


class TestExchangeToken(unittest.TestCase):
    """Tests for exchange_token."""

    def test_successful_exchange(self) -> None:
        from agentos.copilot.auth import exchange_token

        mock_response = MagicMock()
        mock_response.json.return_value = {"token": "ghu_abc123"}
        mock_response.raise_for_status = MagicMock()

        with patch("agentos.copilot.auth.httpx.get", return_value=mock_response) as mock_get:
            result = exchange_token("integration-token-xyz")

        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args
        self.assertIn("Authorization", call_kwargs.kwargs["headers"])
        self.assertEqual(result, "ghu_abc123")

    def test_http_error_propagates(self) -> None:
        import httpx
        from agentos.copilot.auth import exchange_token

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "403 Forbidden", request=MagicMock(), response=MagicMock()
        )

        with patch("agentos.copilot.auth.httpx.get", return_value=mock_response):
            with self.assertRaises(httpx.HTTPStatusError):
                exchange_token("bad-token")


if __name__ == "__main__":
    unittest.main()
