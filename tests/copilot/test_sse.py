"""Tests for agentos.copilot.sse."""

from __future__ import annotations

import asyncio
import json
import unittest


class TestSseText(unittest.TestCase):
    """Tests for sse_text."""

    def setUp(self) -> None:
        from agentos.copilot.sse import sse_text

        self.sse_text = sse_text

    def test_format_basic(self) -> None:
        frame = self.sse_text("Hello")
        self.assertTrue(frame.startswith("data: "))
        self.assertTrue(frame.endswith("\n\n"))

    def test_content_in_payload(self) -> None:
        frame = self.sse_text("world")
        payload = json.loads(frame[len("data: "):].strip())
        self.assertEqual(payload["choices"][0]["delta"]["content"], "world")

    def test_empty_content(self) -> None:
        frame = self.sse_text("")
        payload = json.loads(frame[len("data: "):].strip())
        self.assertEqual(payload["choices"][0]["delta"]["content"], "")

    def test_special_characters(self) -> None:
        text = 'Line 1\nLine 2 & "quoted"'
        frame = self.sse_text(text)
        payload = json.loads(frame[len("data: "):].strip())
        self.assertEqual(payload["choices"][0]["delta"]["content"], text)


class TestSseDone(unittest.TestCase):
    """Tests for sse_done."""

    def test_done_frame(self) -> None:
        from agentos.copilot.sse import sse_done

        frame = sse_done()
        self.assertEqual(frame, "data: [DONE]\n\n")


class TestStreamResponse(unittest.TestCase):
    """Tests for stream_response."""

    def _collect(self, chunks):
        from agentos.copilot.sse import stream_response

        async def _run():
            return [f async for f in stream_response(chunks)]

        return asyncio.run(_run())

    def test_yields_one_frame_per_chunk_plus_done(self) -> None:
        frames = self._collect(["a", "b", "c"])
        self.assertEqual(len(frames), 4)

    def test_last_frame_is_done(self) -> None:
        frames = self._collect(["x"])
        self.assertEqual(frames[-1], "data: [DONE]\n\n")

    def test_content_frames_are_valid_sse(self) -> None:
        frames = self._collect(["hello", " world"])
        for frame in frames[:-1]:  # exclude [DONE]
            self.assertTrue(frame.startswith("data: "))
            payload = json.loads(frame[len("data: "):].strip())
            self.assertIn("choices", payload)

    def test_empty_iterator(self) -> None:
        frames = self._collect([])
        self.assertEqual(frames, ["data: [DONE]\n\n"])


if __name__ == "__main__":
    unittest.main()
