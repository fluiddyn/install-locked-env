"""Tests for file downloading."""

import pytest
from unittest.mock import Mock, patch
import httpx
from install_locked_env.downloaders import download_files_choose_tool
from install_locked_env.parsers import UrlInfo


@pytest.fixture
def mock_url_info():
    """Create a mock UrlInfo object."""
    return UrlInfo(
        platform="github",
        owner="test",
        repo="repo",
        ref="main",
        path="envs/test",
        raw_url_template="https://example.com/{filename}",
    )


def test_download_pixi_files_success(mock_url_info):
    """Test successful download of pixi files."""

    def mock_get(url):
        filename = url.split("/")[-1]

        if filename.startswith("pixi"):
            response = httpx.Response(
                200,
                text="[project]\nname = 'test'"
                if filename == "pixi.toml"
                else "# lock file content",
            )
            response.request = httpx.Request("GET", url)
            return response
        else:
            response = httpx.Response(404, text="Not found")
            response.request = httpx.Request("GET", url)
            raise httpx.HTTPStatusError(
                "404", request=response.request, response=response
            )

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get = mock_get

        tool, files = download_files_choose_tool(mock_url_info)

        assert tool == "pixi"
        assert "pixi.toml" in files
        assert "pixi.lock" in files
        assert files["pixi.toml"] == "[project]\nname = 'test'"
        assert files["pixi.lock"] == "# lock file content"


def test_download_only_pixi_toml(mock_url_info):
    """Test download when only pixi.toml exists."""

    def mock_get(url):
        filename = url.split("/")[-1]
        if filename == "pixi.toml":
            response = httpx.Response(200, text="[project]\nname = 'test'")
            response.request = httpx.Request("GET", url)
            return response
        else:
            response = httpx.Response(404, text="Not found")
            response.request = httpx.Request("GET", url)
            raise httpx.HTTPStatusError(
                "404", request=response.request, response=response
            )

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get = mock_get

        with pytest.raises(ValueError, match="No supported lock files found"):
            tool, files = download_files_choose_tool(mock_url_info)


def test_download_no_files_found(mock_url_info):
    """Test error when no supported files are found."""

    def mock_get(url):
        response = httpx.Response(404, text="Not found")
        response.request = httpx.Request("GET", url)
        raise httpx.HTTPStatusError("404", request=response.request, response=response)

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get = mock_get

        with pytest.raises(ValueError, match="No supported lock files found"):
            download_files_choose_tool(mock_url_info)


@pytest.mark.xfail
def test_download_http_error_propagation(mock_url_info):
    """Test that HTTP errors are properly raised."""

    def mock_get(url):
        filename = url.split("/")[-1]
        if filename == "pixi.toml":
            response = httpx.Response(500, text="Server error")
            response.request = httpx.Request("GET", url)
            raise httpx.HTTPStatusError(
                "500", request=response.request, response=response
            )
        response = httpx.Response(404, text="Not found")
        response.request = httpx.Request("GET", url)
        raise httpx.HTTPStatusError("404", request=response.request, response=response)

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get = mock_get

        # Should raise because server error for pixi.toml
        with pytest.raises(httpx.HTTPStatusError):
            download_files_choose_tool(mock_url_info)
