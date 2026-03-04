"""Gemini vision analysis MCP tool factory.

Provides :func:`make_analyze_image_tool` which creates the ``analyze_image``
MCP tool.  The tool reads an image file from disk, base64-encodes it, and
sends it to the Gemini vision API via ``httpx``.

Configuration:

- ``GEMINI_API_KEY`` (required) — API key for the Gemini REST endpoint.
- ``PYKOCLAW_VISION_MODEL`` — override the vision model (default:
  ``gemini-3.1-flash-lite-preview``).
"""

from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com"

# Default model for vision analysis.
DEFAULT_VISION_MODEL = "gemini-3.1-flash-lite-preview"

# Map file extensions → MIME types for the Gemini payload.
_MEDIA_TYPE_MAP: dict[str, str] = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
}


def make_analyze_image_tool():
    """Create the ``analyze_image`` MCP tool.

    The returned :class:`claude_agent_sdk.SdkMcpTool` reads an image file
    from disk, base64-encodes it, and calls the Gemini vision API using
    ``httpx``.  Reads ``GEMINI_API_KEY`` from the environment; honours
    ``PYKOCLAW_VISION_MODEL`` to override the default model
    (``gemini-3.1-flash-lite-preview``).
    """
    from textwrap import dedent

    from claude_agent_sdk import tool

    @tool(
        "analyze_image",
        dedent("""\
            Analyze an image using Gemini's vision capabilities.
            Call this tool when you receive a message containing an
            <attachment type="image" path="..." /> element.
            Pass the path exactly as it appears in the attachment tag.
            Returns a text description or answer to your question."""),
        {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to the image file on disk.",
                },
                "question": {
                    "type": "string",
                    "description": (
                        "Question or instruction about the image. "
                        "Defaults to a general description request."
                    ),
                },
            },
            "required": ["path"],
        },
    )
    async def analyze_image(args: dict) -> dict:
        import httpx

        path = Path(args["path"])
        question = args.get("question", "Describe this image in detail.")

        if not path.exists():
            return {"content": [{"type": "text", "text": f"File not found: {path}"}]}

        suffix = path.suffix.lower().lstrip(".")
        media_type = _MEDIA_TYPE_MAP.get(suffix, "image/jpeg")

        try:
            raw = path.read_bytes()
        except OSError as exc:
            return {"content": [{"type": "text", "text": f"Cannot read image: {exc}"}]}

        image_data = base64.standard_b64encode(raw).decode()

        api_key = os.environ.get("GEMINI_API_KEY", "")
        vision_model = os.environ.get("PYKOCLAW_VISION_MODEL", DEFAULT_VISION_MODEL)

        payload = {
            "contents": [
                {
                    "parts": [
                        {"inline_data": {"mime_type": media_type, "data": image_data}},
                        {"text": question},
                    ]
                }
            ]
        }

        url = (
            f"{_GEMINI_BASE_URL}/v1beta/models/{vision_model}"
            f":generateContent?key={api_key}"
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as http:
                resp = await http.post(
                    url,
                    headers={"content-type": "application/json"},
                    json=payload,
                )
            resp.raise_for_status()
            data = resp.json()
            text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text")
                or "No description returned."
            )
            return {"content": [{"type": "text", "text": text}]}
        except Exception as exc:
            log.exception("Vision API call failed for %s", path)
            return {
                "content": [{"type": "text", "text": f"Image analysis failed: {exc}"}]
            }

    return analyze_image
