"""Tests for the pykoclaw-vision analyze_image MCP tool."""

from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from pykoclaw_vision import make_analyze_image_tool
from pykoclaw_vision.vision import DEFAULT_VISION_MODEL, _GEMINI_BASE_URL


@pytest.fixture
def sample_image(tmp_path: Path) -> Path:
    p = tmp_path / "test.jpg"
    p.write_bytes(b"\xff\xd8\xff" + b"\x00" * 16)
    return p


@pytest.mark.asyncio
async def test_analyze_image_success(sample_image: Path) -> None:
    tool_fn = make_analyze_image_tool()

    gemini_response = {
        "candidates": [{"content": {"parts": [{"text": "A test image."}]}}]
    }

    mock_resp = Mock()
    mock_resp.raise_for_status = Mock()
    mock_resp.json.return_value = gemini_response

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_resp)

    with patch("httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            result = await tool_fn.handler(
                {"path": str(sample_image), "question": "What is this?"}
            )

    assert result["content"][0]["text"] == "A test image."

    call_kwargs = mock_client.post.call_args
    url = call_kwargs[0][0]
    assert _GEMINI_BASE_URL in url
    assert DEFAULT_VISION_MODEL in url
    assert "test-key" in url

    payload = call_kwargs[1]["json"]
    parts = payload["contents"][0]["parts"]
    assert parts[0]["inline_data"]["mime_type"] == "image/jpeg"
    assert parts[1]["text"] == "What is this?"
    assert base64.standard_b64decode(parts[0]["inline_data"]["data"])


@pytest.mark.asyncio
async def test_analyze_image_custom_model(sample_image: Path) -> None:
    tool_fn = make_analyze_image_tool()

    mock_resp = Mock()
    mock_resp.raise_for_status = Mock()
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "ok"}]}}]
    }

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_resp)

    with patch("httpx.AsyncClient", return_value=mock_client):
        with patch.dict(
            "os.environ",
            {"GEMINI_API_KEY": "key", "PYKOCLAW_VISION_MODEL": "gemini-custom"},
        ):
            await tool_fn.handler({"path": str(sample_image)})

    url = mock_client.post.call_args[0][0]
    assert "gemini-custom" in url


@pytest.mark.asyncio
async def test_analyze_image_default_question(sample_image: Path) -> None:
    """Omitting the question argument uses the default description prompt."""
    tool_fn = make_analyze_image_tool()

    mock_resp = Mock()
    mock_resp.raise_for_status = Mock()
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "ok"}]}}]
    }

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_resp)

    with patch("httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "key"}):
            await tool_fn.handler({"path": str(sample_image)})

    payload = mock_client.post.call_args[1]["json"]
    question_part = payload["contents"][0]["parts"][1]["text"]
    assert "describe" in question_part.lower()


@pytest.mark.asyncio
async def test_analyze_image_file_not_found(tmp_path: Path) -> None:
    tool_fn = make_analyze_image_tool()
    result = await tool_fn.handler({"path": str(tmp_path / "missing.jpg")})
    assert "not found" in result["content"][0]["text"].lower()


@pytest.mark.asyncio
async def test_analyze_image_api_failure(sample_image: Path) -> None:
    tool_fn = make_analyze_image_tool()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(side_effect=RuntimeError("connection refused"))

    with patch("httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "key"}):
            result = await tool_fn.handler({"path": str(sample_image)})

    assert "failed" in result["content"][0]["text"].lower()


@pytest.mark.asyncio
async def test_analyze_image_png(tmp_path: Path) -> None:
    """PNG files are passed with the correct MIME type."""
    png = tmp_path / "shot.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)
    tool_fn = make_analyze_image_tool()

    mock_resp = Mock()
    mock_resp.raise_for_status = Mock()
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "png image"}]}}]
    }

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_resp)

    with patch("httpx.AsyncClient", return_value=mock_client):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "key"}):
            await tool_fn.handler({"path": str(png)})

    payload = mock_client.post.call_args[1]["json"]
    assert payload["contents"][0]["parts"][0]["inline_data"]["mime_type"] == "image/png"
