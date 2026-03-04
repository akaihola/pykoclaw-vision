"""pykoclaw-vision — shared Gemini vision/image-generation MCP tools.

Provides factory functions for MCP tools that call the Gemini API:

- :func:`make_analyze_image_tool` — ``analyze_image`` tool for vision
  analysis (``gemini-3.1-flash-lite-preview`` by default).

Channel plugins import these factories and include the resulting tools in
their MCP server rather than each duplicating the Gemini client code.

Configuration via environment variables:

- ``GEMINI_API_KEY`` (required)
- ``PYKOCLAW_VISION_MODEL`` — override the vision model
- ``PYKOCLAW_IMAGE_MODEL`` — override the image-generation model
"""

from pykoclaw_vision.vision import make_analyze_image_tool

__all__ = ["make_analyze_image_tool"]
