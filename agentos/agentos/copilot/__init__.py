"""
AgentOS Copilot Extension package.

This sub-package implements a GitHub Copilot Extension that exposes AgentOS
capabilities directly inside GitHub Copilot Chat.  Users interact with the
extension by typing ``@agentos <command>`` in any Copilot Chat surface
(VS Code, GitHub.com, GitHub Mobile).

Quick start
-----------
Install the optional dependencies::

    pip install 'agentos[copilot]'

Start the server::

    python -m agentos copilot-serve --port 3000 --secret $WEBHOOK_SECRET

Or programmatically::

    from agentos.copilot import create_app
    import uvicorn
    app = create_app(secret="my-secret")
    uvicorn.run(app, host="0.0.0.0", port=3000)

Public API
----------
* :func:`create_app` – build the FastAPI ASGI app.
* :func:`main` – ``argparse``-based CLI entry point.
"""

from .server import create_app, main

__all__ = ["create_app", "main"]
