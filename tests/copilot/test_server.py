"""Integration tests for the AgentOS Copilot Extension server."""

from __future__ import annotations

import hashlib
import hmac
import json
import unittest


def _make_sig(payload: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _copilot_body(user_text: str) -> bytes:
    """Build a minimal Copilot-style request body."""
    return json.dumps({"messages": [{"role": "user", "content": user_text}]}).encode()


class TestServerHealth(unittest.TestCase):
    """Tests for the /health endpoint."""

    def setUp(self) -> None:
        from fastapi.testclient import TestClient
        from agentos.copilot.server import create_app

        self.client = TestClient(create_app())

    def test_health_returns_200(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


class TestServerNoSecret(unittest.TestCase):
    """Tests for requests when no webhook secret is configured."""

    def setUp(self) -> None:
        from fastapi.testclient import TestClient
        from agentos.copilot.server import create_app

        self.client = TestClient(create_app(secret=None))

    def test_help_request_returns_200(self) -> None:
        body = _copilot_body("help")
        response = self.client.post(
            "/",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)

    def test_response_is_event_stream(self) -> None:
        body = _copilot_body("help")
        response = self.client.post(
            "/",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        self.assertIn("text/event-stream", response.headers.get("content-type", ""))

    def test_sse_stream_contains_done(self) -> None:
        body = _copilot_body("help")
        response = self.client.post(
            "/",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        self.assertIn("[DONE]", response.text)

    def test_invalid_json_returns_400(self) -> None:
        response = self.client.post(
            "/",
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 400)

    def test_empty_messages_falls_back_to_help(self) -> None:
        body = json.dumps({"messages": []}).encode()
        response = self.client.post(
            "/",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("AgentOS", response.text)

    def test_discover_command_in_stream(self) -> None:
        from unittest.mock import patch

        fake_standards = {
            "max_line_length": 79,
            "average_line_length": 40.0,
            "functions_with_docstrings": 1.0,
            "variable_naming_style": "snake_case",
            "files_scanned": 3,
        }
        with patch("agentos.copilot.handlers.discover_standards", return_value=fake_standards):
            body = _copilot_body("discover .")
            response = self.client.post(
                "/",
                content=body,
                headers={"Content-Type": "application/json"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn("snake_case", response.text)

    def test_spec_command_in_stream(self) -> None:
        body = _copilot_body('spec title="Auth Feature"')
        response = self.client.post(
            "/",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Auth Feature", response.text)

    def test_run_command_in_stream(self) -> None:
        body = _copilot_body('run code="def run(): return 99"')
        response = self.client.post(
            "/",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("99", response.text)


class TestServerWithSecret(unittest.TestCase):
    """Tests for requests when a webhook secret is configured."""

    SECRET = "super-secret-key"

    def setUp(self) -> None:
        from fastapi.testclient import TestClient
        from agentos.copilot.server import create_app

        self.client = TestClient(create_app(secret=self.SECRET))

    def test_valid_signature_accepted(self) -> None:
        body = _copilot_body("help")
        sig = _make_sig(body, self.SECRET)
        response = self.client.post(
            "/",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": sig,
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_missing_signature_returns_401(self) -> None:
        body = _copilot_body("help")
        response = self.client.post(
            "/",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 401)

    def test_wrong_signature_returns_401(self) -> None:
        body = _copilot_body("help")
        bad_sig = _make_sig(body, "wrong-secret")
        response = self.client.post(
            "/",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": bad_sig,
            },
        )
        self.assertEqual(response.status_code, 401)

    def test_tampered_body_returns_401(self) -> None:
        original = _copilot_body("help")
        sig = _make_sig(original, self.SECRET)
        tampered = _copilot_body("inject")  # different body
        response = self.client.post(
            "/",
            content=tampered,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": sig,
            },
        )
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
