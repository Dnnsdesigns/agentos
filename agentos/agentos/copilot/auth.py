"""
Authentication helpers for the AgentOS Copilot Extension.

This module provides two functions:

* :func:`verify_signature` – validates the HMAC-SHA256 signature that GitHub
  attaches to every webhook delivery.  If the extension is configured without
  a secret the function short-circuits to ``True`` so that local development
  does not require a real GitHub App.

* :func:`exchange_token` – calls GitHub's token exchange endpoint to swap the
  short-lived ``X-GitHub-Token`` header value for a user-scoped OAuth access
  token.  This token can be used to make GitHub API calls on behalf of the
  authenticated Copilot user, for example to read repository contents when
  running :func:`agentos.standards.discover_standards`.
"""

from __future__ import annotations

import hashlib
import hmac

import httpx

# GitHub token exchange endpoint used by Copilot Extensions.
_TOKEN_EXCHANGE_URL = "https://api.github.com/copilot_internal/v2/token"


def verify_signature(payload: bytes, sig_header: str, secret: str) -> bool:
    """Verify the HMAC-SHA256 signature of an incoming webhook payload.

    GitHub signs every webhook delivery with the app's webhook secret using
    HMAC-SHA256.  The resulting digest is sent in the
    ``X-Hub-Signature-256`` request header in the form ``sha256=<hex>``.

    Parameters
    ----------
    payload:
        The raw request body bytes as received from the HTTP server.
    sig_header:
        The value of the ``X-Hub-Signature-256`` request header, e.g.
        ``"sha256=abc123..."``.
    secret:
        The webhook secret configured on the GitHub App.

    Returns
    -------
    bool
        ``True`` if the signature is valid, ``False`` otherwise.

    Notes
    -----
    The comparison is performed using :func:`hmac.compare_digest` to
    prevent timing attacks.
    """
    if not sig_header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    received = sig_header[len("sha256="):]
    return hmac.compare_digest(expected, received)


def exchange_token(integration_token: str) -> str:
    """Exchange a Copilot integration token for a user-scoped access token.

    GitHub Copilot Extensions receive a short-lived token in the
    ``X-GitHub-Token`` request header.  This token can be exchanged for a
    full user-scoped OAuth access token by calling GitHub's internal token
    exchange endpoint.  The resulting token can then be used for GitHub API
    calls on behalf of the authenticated user.

    Parameters
    ----------
    integration_token:
        The value of the ``X-GitHub-Token`` request header.

    Returns
    -------
    str
        A user-scoped OAuth access token.

    Raises
    ------
    httpx.HTTPStatusError
        If GitHub's token exchange endpoint returns a non-2xx response.
    """
    response = httpx.get(
        _TOKEN_EXCHANGE_URL,
        headers={"Authorization": f"Bearer {integration_token}"},
    )
    response.raise_for_status()
    return response.json()["token"]
