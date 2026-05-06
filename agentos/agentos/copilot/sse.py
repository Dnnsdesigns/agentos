"""
Server-Sent Events (SSE) helpers for the AgentOS Copilot Extension.

GitHub Copilot Extensions must return responses as a stream of SSE frames
that follow the OpenAI chat-completion delta format.  This module provides
the formatting primitives and an async generator that turns an iterable of
text chunks into a complete SSE stream.

Each data frame carries a JSON object with a single delta content token::

    data: {"choices":[{"delta":{"content":"Hello"}}]}

The stream is terminated by a final frame::

    data: [DONE]

References
----------
* GitHub Copilot Extension docs – response streaming:
  https://docs.github.com/en/copilot/building-copilot-extensions/building-a-copilot-agent-for-your-copilot-extension
"""

from __future__ import annotations

import json
from typing import AsyncGenerator, Iterable


def sse_text(content: str) -> str:
    """Format a single SSE delta frame containing a text chunk.

    Parameters
    ----------
    content:
        The text fragment to include in the delta.

    Returns
    -------
    str
        A complete SSE ``data:`` line terminated by the required double
        newline (``\\n\\n``).

    Examples
    --------
    >>> sse_text("Hello")
    'data: {"choices": [{"delta": {"content": "Hello"}}]}\\n\\n'
    """
    payload = {"choices": [{"delta": {"content": content}}]}
    return f"data: {json.dumps(payload)}\n\n"


def sse_done() -> str:
    """Return the terminal SSE frame that signals end-of-stream.

    Returns
    -------
    str
        The ``data: [DONE]`` frame followed by a double newline.

    Examples
    --------
    >>> sse_done()
    'data: [DONE]\\n\\n'
    """
    return "data: [DONE]\n\n"


async def stream_response(chunks: Iterable[str]) -> AsyncGenerator[str, None]:
    """Yield SSE frames for each text chunk followed by a ``[DONE]`` frame.

    This async generator can be passed directly to FastAPI's
    :class:`fastapi.responses.StreamingResponse`.

    Parameters
    ----------
    chunks:
        An iterable of text fragments.  Each fragment becomes one SSE
        delta frame.

    Yields
    ------
    str
        Formatted SSE frames suitable for a ``text/event-stream`` response.

    Examples
    --------
    >>> import asyncio
    >>> async def collect():
    ...     return [f async for f in stream_response(["Hi", " there"])]
    >>> frames = asyncio.run(collect())
    >>> len(frames)
    3
    """
    try:
        for chunk in chunks:
            yield sse_text(chunk)
    except Exception as exc:
        # Catch any unexpected exception from a handler generator and surface
        # a sanitized error message rather than letting a raw traceback
        # propagate into the response stream.
        yield sse_text(f"⚠️ Internal error: {type(exc).__name__}: {exc}\n")
    yield sse_done()
