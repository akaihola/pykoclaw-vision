# pykoclaw-vision

[![Built with Claude Code](https://img.shields.io/badge/Built_with-Claude_Code-6f42c1?logo=anthropic&logoColor=white)](https://claude.ai/code)

> This project is developed by an AI coding agent ([Claude Code][claude-code]), with human oversight and direction.

Shared vision helper library for public [pykoclaw][pykoclaw] plugins. This
repository is a separate support package inside the private `pykoclaw-dev` uv
workspace. It currently provides a factory for the `analyze_image` MCP tool,
which reads an image from local disk and sends it to the Gemini API for
description or question-answering.

## Features

- **`analyze_image` MCP tool** — channel plugins can register a shared image
  analysis tool instead of duplicating Gemini client code.
- **Local file input** — reads absolute image paths from disk.
- **Gemini REST integration** — sends base64-encoded image data to the Gemini
  `generateContent` endpoint.
- **Format support** — JPEG, PNG, GIF, and WebP.
- **Configurable model** — defaults to `gemini-3.1-flash-lite-preview` and can
  be overridden with `PYKOCLAW_VISION_MODEL`.

## Usage

This package is not a standalone CLI plugin. Instead, channel plugins import
`make_analyze_image_tool()` and include the returned tool in their MCP server.

Current users in this workspace:

- `pykoclaw-whatsapp`
- `pykoclaw-slack`

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | — | Required Gemini API key |
| `PYKOCLAW_VISION_MODEL` | `gemini-3.1-flash-lite-preview` | Override the vision model |

## Installation

```bash
uv pip install pykoclaw-vision@git+https://github.com/akaihola/pykoclaw-vision.git
```

Within the development workspace, `uv sync` already wires it into dependent
packages.

[claude-code]: https://claude.ai/code
[pykoclaw]: https://github.com/akaihola/pykoclaw
