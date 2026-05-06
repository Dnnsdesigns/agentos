"""
FastAPI application and entry point for the AgentOS Copilot Extension server.

This module builds an ASGI application that acts as a GitHub Copilot
Extension backend.  GitHub's Copilot Gateway forwards chat messages here as
HTTP POST requests.  The server:

1. Optionally verifies the HMAC-SHA256 webhook signature.
2. Parses the Copilot request body to extract the conversation messages.
3. Routes the last user message to an AgentOS handler via
   :func:`agentos.copilot.handlers.dispatch`.
4. Streams the handler output back as Server-Sent Events (SSE) using the
   OpenAI delta format that Copilot expects.

Usage
-----
Start the server directly::

    python -m agentos copilot-serve --host 0.0.0.0 --port 3000

Or programmatically::

    from agentos.copilot.server import create_app
    import uvicorn
    app = create_app(secret="my-webhook-secret")
    uvicorn.run(app, host="0.0.0.0", port=3000)
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse

from .auth import verify_signature
from .handlers import dispatch
from .router import parse_intent
from .sse import stream_response


def create_app(secret: Optional[str] = None) -> FastAPI:
    """Build and return the AgentOS Copilot Extension ASGI application.

    Parameters
    ----------
    secret:
        The webhook secret configured on the GitHub App.  When provided,
        every incoming request must carry a valid ``X-Hub-Signature-256``
        header.  Omit (or pass ``None``) to skip signature verification,
        which is convenient during local development.

    Returns
    -------
    FastAPI
        A configured ASGI application ready to be served by uvicorn.
    """
    app = FastAPI(
        title="AgentOS Copilot Extension",
        description=(
            "GitHub Copilot Extension that exposes AgentOS capabilities "
            "inside Copilot Chat."
        ),
        version="0.1.0",
    )

    @app.post("/")
    async def copilot_handler(request: Request) -> StreamingResponse:
        """Handle an incoming GitHub Copilot Extension webhook request.

        The endpoint:

        * Verifies the ``X-Hub-Signature-256`` header when a secret is
          configured.
        * Reads and parses the JSON body to extract the ``messages`` array.
        * Routes the conversation to the appropriate AgentOS handler.
        * Streams the response as ``text/event-stream`` SSE frames.

        Returns
        -------
        StreamingResponse
            A streaming SSE response containing the handler output.

        Raises
        ------
        HTTPException
            ``401`` if signature verification fails.
            ``400`` if the request body cannot be parsed as JSON.
        """
        raw_body = await request.body()

        # -- Signature verification -------------------------------------------
        if secret is not None:
            sig = request.headers.get("X-Hub-Signature-256", "")
            if not verify_signature(raw_body, sig, secret):
                raise HTTPException(status_code=401, detail="Invalid signature")

        # -- Parse body -------------------------------------------------------
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")

        messages = body.get("messages", [])

        # -- Dispatch ---------------------------------------------------------
        intent = parse_intent(messages)
        chunks = dispatch(intent)

        return StreamingResponse(
            stream_response(chunks),
            media_type="text/event-stream",
        )

    @app.get("/health")
    async def health() -> dict:
        """Simple health-check endpoint.

        Returns
        -------
        dict
            ``{"status": "ok"}``
        """
        return {"status": "ok"}

    return app


def main(argv: Optional[list] = None) -> int:
    """Entry point for the ``copilot-serve`` CLI subcommand.

    Parameters
    ----------
    argv:
        Optional argument list (defaults to ``sys.argv[1:]``).

    Returns
    -------
    int
        Exit code (0 on success).
    """
    try:
        import uvicorn
    except ImportError:
        print(
            "uvicorn is required to run the Copilot Extension server.\n"
            "Install it with: pip install 'agentos[copilot]'",
            file=sys.stderr,
        )
        return 1

    parser = argparse.ArgumentParser(
        description="Start the AgentOS GitHub Copilot Extension server",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host address to bind (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="TCP port to listen on (default: 3000)",
    )
    parser.add_argument(
        "--secret",
        default=None,
        help=(
            "Webhook secret configured on the GitHub App.  "
            "If omitted, signature verification is disabled."
        ),
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development (requires watchfiles)",
    )

    args = parser.parse_args(argv)
    app = create_app(secret=args.secret)

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
