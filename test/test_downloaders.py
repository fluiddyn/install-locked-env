"""Test suite for file downloading utilities."""

import os
import shutil
import tempfile
from unittest.mock import Mock, patch

import httpx
import pytest

from install_locked_env.parsers import UrlInfo
from install_locked_env.downloaders import (
    download_files_choose_tool,
    download_via_archive,
    download_via_clone,
    download_file_per_file,
    download_repo_files,
)


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
        base_url="https://example.com",
    )


def test_download_pixi_files_success(mock_url_info):
    """Test successful download of pixi files."""

    def mock_get(url):
        filename = url.split("/")[-1]

        if filename.startswith("pixi"):
            response = httpx.Response(
                200,
                text=(
                    "[project]\nname = 'test'"
                    if filename == "pixi.toml"
                    else "# lock file content"
                ),
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


@pytest.fixture
def github_url_info():
    """Sample GitHub URL info."""
    return UrlInfo(
        platform="github",
        owner="test-owner",
        repo="test-repo",
        ref="main",
        path="",
        raw_url_template="https://raw.githubusercontent.com/test-owner/test-repo/{ref}/{filename}",
        base_url="https://github.com",
    )


@pytest.fixture
def gitlab_url_info():
    """Sample GitLab URL info."""
    return UrlInfo(
        platform="gitlab",
        owner="test-owner",
        repo="test-repo",
        ref="main",
        path="",
        raw_url_template="https://gitlab.com/test-owner/test-repo/-/raw/{ref}/{filename}",
        base_url="https://gitlab.com",
    )


@pytest.fixture
def heptapod_url_info():
    """Sample Heptapod URL info."""
    return UrlInfo(
        platform="heptapod",
        owner="test-owner",
        repo="test-repo",
        ref="default",
        path="",
        raw_url_template="https://foss.heptapod.net/test-owner/test-repo/-/raw/{ref}/{filename}",
        base_url="https://foss.heptapod.net",
    )


class TestDownloadViaArchive:
    """Tests for download_via_archive function."""

    @patch("install_locked_env.downloaders.requests.get")
    @patch("install_locked_env.downloaders.zipfile.ZipFile")
    def test_downloads_github_archive(
        self, mock_zipfile, mock_requests_get, github_url_info, tmp_path
    ):
        """Test downloading GitHub repository as zip archive."""
        dest_dir = tmp_path / "test-repo"

        # Mock the HTTP response
        mock_response = Mock()
        mock_response.iter_content = Mock(return_value=[b"fake zip content"])
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        # Mock zipfile extraction
        mock_zip = Mock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip

        # Create a fake extracted directory
        extracted_dir = os.path.join(tmp_path, "extracted")
        os.makedirs(extracted_dir)
        fake_content_dir = os.path.join(extracted_dir, "test-repo-main")
        os.makedirs(fake_content_dir)

        with patch(
            "install_locked_env.downloaders.tempfile.mkdtemp",
            return_value=extracted_dir,
        ):
            with patch("os.listdir", return_value=["test-repo-main"]):
                with patch("shutil.move"):
                    download_via_archive(github_url_info, dest_dir)

        # Verify the correct URL was called
        called_url = mock_requests_get.call_args[0][0]
        assert "github.com" in called_url
        assert "archive/refs/heads/main.zip" in called_url

    @patch("install_locked_env.downloaders.requests.get")
    @patch("install_locked_env.downloaders.tarfile.open")
    def test_downloads_gitlab_archive(
        self, mock_tarfile, mock_requests_get, gitlab_url_info, tmp_path
    ):
        """Test downloading GitLab repository as tar.gz archive."""
        dest_dir = tmp_path / "test-repo"

        # Mock the HTTP response
        mock_response = Mock()
        mock_response.iter_content = Mock(return_value=[b"fake tar content"])
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        # Mock tarfile extraction
        mock_tar = Mock()
        mock_tarfile.return_value.__enter__.return_value = mock_tar

        # Create a fake extracted directory
        extracted_dir = os.path.join(tmp_path, "extracted")
        os.makedirs(extracted_dir)
        fake_content_dir = os.path.join(extracted_dir, "test-repo-main")
        os.makedirs(fake_content_dir)

        with patch(
            "install_locked_env.downloaders.tempfile.mkdtemp",
            return_value=extracted_dir,
        ):
            with patch("os.listdir", return_value=["test-repo-main"]):
                with patch("shutil.move"):
                    download_via_archive(gitlab_url_info, dest_dir)

        # Verify the correct URL was called
        called_url = mock_requests_get.call_args[0][0]
        assert "gitlab.com" in called_url
        assert "/-/archive/main/" in called_url
        assert ".tar.gz" in called_url

    @patch("install_locked_env.downloaders.requests.get")
    def test_handles_ref_with_slashes_gitlab(self, mock_requests_get, tmp_path):
        """Test that refs with slashes are properly handled for GitLab."""
        url_info = UrlInfo(
            platform="gitlab",
            owner="test-owner",
            repo="test-repo",
            ref="feature/new-feature",
            path="",
            raw_url_template="",
            base_url="https://gitlab.com",
        )

        mock_response = Mock()
        mock_response.iter_content = Mock(return_value=[b"content"])
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        with patch("install_locked_env.downloaders.tarfile.open"):
            with patch("install_locked_env.downloaders.tempfile.mkdtemp"):
                with patch("os.listdir", return_value=["extracted"]):
                    with patch("shutil.move"):
                        with patch("shutil.rmtree"):
                            dest_dir = os.path.join(tmp_path, "test")
                            download_via_archive(url_info, dest_dir)

        # Verify slashes are replaced with dashes
        called_url = mock_requests_get.call_args[0][0]
        assert "feature-new-feature" in called_url


class TestDownloadViaClone:
    """Tests for download_via_clone function."""

    @patch("install_locked_env.downloaders.subprocess.run")
    def test_clones_github_with_git(self, mock_subprocess, github_url_info, tmp_path):
        """Test cloning GitHub repository with git."""
        dest_dir = tmp_path / "test-repo"

        download_via_clone(github_url_info, dest_dir)

        # Verify git clone was called
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert call_args[0] == "git"
        assert call_args[1] == "clone"
        assert "--depth" in call_args
        assert "--branch" in call_args
        assert "main" in call_args

    @patch("install_locked_env.downloaders.subprocess.run")
    @patch("install_locked_env.downloaders._get_heptapod_vcs_type", return_value="hg")
    def test_clones_heptapod_with_hg(
        self, mock_vcs_type, mock_subprocess, heptapod_url_info, tmp_path
    ):
        """Test cloning Heptapod repository with mercurial."""
        dest_dir = tmp_path / "test-repo"

        download_via_clone(heptapod_url_info, dest_dir)

        # Verify hg clone was called
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert call_args[0] == "hg"
        assert call_args[1] == "clone"
        assert "--rev" in call_args

    def test_raises_when_path_specified(self, github_url_info, tmp_path):
        """Test raises ValueError when trying to clone with path specified."""
        url_info_with_path = UrlInfo(
            platform="github",
            owner="test-owner",
            repo="test-repo",
            ref="main",
            path="src/utils",
            raw_url_template="",
            base_url="https://github.com",
        )

        dest_dir = tmp_path / "test-repo"

        with pytest.raises(
            ValueError, match="Clone only supported for full repository"
        ):
            download_via_clone(url_info_with_path, dest_dir)


class TestDownloadFilePerFile:
    """Tests for download_file_per_file function."""

    @patch("install_locked_env.downloaders._download_github")
    def test_calls_github_downloader(
        self, mock_download_github, github_url_info, tmp_path
    ):
        """Test that GitHub downloader is called."""
        dest_dir = tmp_path / "test-repo"
        os.makedirs(dest_dir)

        download_file_per_file(github_url_info, dest_dir)

        mock_download_github.assert_called_once_with(github_url_info, dest_dir)

    @patch("install_locked_env.downloaders._download_gitlab")
    def test_calls_gitlab_downloader(
        self, mock_download_gitlab, gitlab_url_info, tmp_path
    ):
        """Test that GitLab downloader is called."""
        dest_dir = tmp_path / "test-repo"
        os.makedirs(dest_dir)

        download_file_per_file(gitlab_url_info, dest_dir)

        mock_download_gitlab.assert_called_once_with(gitlab_url_info, dest_dir)

    @patch("install_locked_env.downloaders._download_gitlab")
    def test_calls_gitlab_downloader_for_heptapod(
        self, mock_download_gitlab, heptapod_url_info, tmp_path
    ):
        """Test that GitLab downloader is used for Heptapod."""
        dest_dir = tmp_path / "test-repo"
        os.makedirs(dest_dir)

        download_file_per_file(heptapod_url_info, dest_dir)

        mock_download_gitlab.assert_called_once_with(heptapod_url_info, dest_dir)


class TestDownloadRepoFiles:
    """Tests for download_repo_files function."""

    def test_raises_when_dest_exists(self, github_url_info, tmp_path):
        """Test raises error when destination directory already exists."""
        dest_dir = tmp_path / "test-repo"
        os.makedirs(dest_dir)

        with pytest.raises(SystemExit):
            download_repo_files(github_url_info, dest_dir)

    @patch("install_locked_env.downloaders.download_via_archive")
    def test_auto_selects_archive_for_full_repo(
        self, mock_download_archive, github_url_info, tmp_path
    ):
        """Test auto mode selects archive for full repository."""
        dest_dir = tmp_path / "test-repo"

        download_repo_files(github_url_info, dest_dir, method="auto")

        mock_download_archive.assert_called_once_with(github_url_info, dest_dir)

    @patch("install_locked_env.downloaders.download_file_per_file")
    def test_auto_selects_file_per_file_for_path(self, mock_download_files, tmp_path):
        """Test auto mode selects file-per-file for specific path."""
        url_info_with_path = UrlInfo(
            platform="github",
            owner="test-owner",
            repo="test-repo",
            ref="main",
            path="src/utils",
            raw_url_template="",
            base_url="https://github.com",
        )

        dest_dir = tmp_path / "test-repo"

        download_repo_files(url_info_with_path, dest_dir, method="auto")

        mock_download_files.assert_called_once_with(url_info_with_path, dest_dir)

    @patch("install_locked_env.downloaders.download_via_clone")
    def test_explicit_clone_method(
        self, mock_download_clone, github_url_info, tmp_path
    ):
        """Test explicitly selecting clone method."""
        dest_dir = tmp_path / "test-repo"

        download_repo_files(github_url_info, dest_dir, method="clone")

        mock_download_clone.assert_called_once_with(github_url_info, dest_dir)

    @patch("install_locked_env.downloaders.download_via_archive")
    def test_explicit_archive_method(
        self, mock_download_archive, github_url_info, tmp_path
    ):
        """Test explicitly selecting archive method."""
        dest_dir = tmp_path / "test-repo"

        download_repo_files(github_url_info, dest_dir, method="archive")

        mock_download_archive.assert_called_once_with(github_url_info, dest_dir)

    @patch("install_locked_env.downloaders.download_file_per_file")
    def test_explicit_file_per_file_method(
        self, mock_download_files, github_url_info, tmp_path
    ):
        """Test explicitly selecting file-per-file method."""
        dest_dir = tmp_path / "test-repo"

        download_repo_files(github_url_info, dest_dir, method="file-per-file")

        mock_download_files.assert_called_once_with(github_url_info, dest_dir)

    def test_raises_with_invalid_method(self, github_url_info, tmp_path):
        """Test raises ValueError with invalid method."""
        dest_dir = tmp_path / "test-repo"

        with pytest.raises(ValueError, match="method has to be in"):
            download_repo_files(github_url_info, dest_dir, method="invalid")

    def test_raises_when_clone_with_path(self, tmp_path):
        """Test raises ValueError when trying to clone with path."""
        url_info_with_path = UrlInfo(
            platform="github",
            owner="test-owner",
            repo="test-repo",
            ref="main",
            path="src/utils",
            raw_url_template="",
            base_url="https://github.com",
        )

        dest_dir = tmp_path / "test-repo"

        with pytest.raises(ValueError, match="only supported for full repository"):
            download_repo_files(url_info_with_path, dest_dir, method="clone")


# Integration-like tests (can be marked as slow/integration tests)
class TestIntegration:
    """Integration tests that test multiple components together."""

    @pytest.mark.slow
    @patch("install_locked_env.downloaders.requests.get")
    @patch("install_locked_env.downloaders.zipfile.ZipFile")
    def test_full_workflow_github_archive(
        self, mock_zipfile, mock_requests_get, github_url_info, tmp_path
    ):
        """Test complete workflow for GitHub archive download."""
        dest_dir = tmp_path / "test-repo"

        # Mock responses
        mock_response = Mock()
        mock_response.iter_content = Mock(return_value=[b"content"])
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        mock_zip = Mock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip

        extracted_dir = os.path.join(tmp_path, "extracted")
        os.makedirs(extracted_dir)
        fake_content = os.path.join(extracted_dir, "content")
        os.makedirs(fake_content)

        with patch(
            "install_locked_env.downloaders.tempfile.mkdtemp",
            return_value=extracted_dir,
        ):
            with patch("os.listdir", return_value=["content"]):
                with patch("shutil.move"):
                    result = download_repo_files(
                        github_url_info, dest_dir, method="archive"
                    )

        assert result == dest_dir
