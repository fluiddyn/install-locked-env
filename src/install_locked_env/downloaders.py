"""File downloading utilities."""

import os
import subprocess
import shutil
import sys
import tarfile
import tempfile
import zipfile

from pathlib import Path
from typing import Literal, Any

import httpx
import requests

from .parsers import UrlInfo


tools_files = {
    "uv-pylock-pdm": ["pyproject.toml", "pylock.toml", "pdm.toml"],
    "pdm-uv": ["pyproject.toml", "pdm.lock", "pdm.toml"],
    "uv-pylock": ["pyproject.toml", "pylock.toml"],
    "uv-pylock-alone": ["pylock.toml"],
    "pixi": ["pixi.toml", "pixi.lock"],
    "uv": ["pyproject.toml", "uv.lock"],
    "pdm": ["pyproject.toml", "pdm.lock"],
    # not yet supported
    # "poetry": ["pyproject.toml", "poetry.lock"],
}


def download_files_choose_tool(url_info: UrlInfo) -> tuple[str, dict[str, str]]:
    """Download environment files from the repository.

    Args:
        url_info: Parsed URL information

    Returns:
        Dictionary mapping filename to file content

    Raises:
        httpx.HTTPError: If download fails
    """
    # Try to detect environment type by attempting to download different lock files
    files = {}

    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
        for tool, file_names in tools_files.items():
            for file_name in file_names:
                if file_name not in files:
                    try:
                        url = url_info.raw_url_template.format(filename=file_name)
                        response = client.get(url)
                        response.raise_for_status()
                        files[file_name] = response.text
                    except httpx.HTTPStatusError:
                        # File doesn't exist, try next
                        continue

            if all(file_name in files for file_name in file_names):
                files = {name: files[name] for name in file_names}
                return tool, files

        for_error = ", ".join("/".join(names) for names in tools_files.values())
        raise ValueError(
            f"No supported lock files found at {url_info.path}. Looked for: {for_error}"
        )


def detect_env_type_from_dir(path_dir: Path) -> str:
    """Detect env type from a directory"""
    names = set(path.name for path in path_dir.glob("*"))
    for tool, file_names in tools_files.items():
        if all(file_name in names for file_name in file_names):
            return tool


def download_via_archive(url_info: UrlInfo, dest_dir: Path) -> None:
    """
    Download repository as an archive file (zip/tar.gz).

    Args:
        url_info: Repository information
        dest_dir: Destination directory
    """
    # Construct archive download URL based on platform
    if url_info.platform == "github":
        # GitHub: https://github.com/owner/repo/archive/refs/heads/branch.zip
        ref = url_info.ref
        archive_url = f"https://github.com/{url_info.owner}/{url_info.repo}/archive/refs/heads/{ref}.zip"
        archive_format = "zip"
    elif url_info.platform in ("gitlab", "heptapod"):
        # GitLab/Heptapod: https://gitlab.com/owner/repo/-/archive/branch/repo-branch.tar.gz
        ref = url_info.ref
        archive_url = (
            f"{url_info.base_url}/{url_info.owner}/{url_info.repo}"
            f"/-/archive/{ref}/{url_info.repo}-{ref.replace('/', '-')}.tar.gz"
        )
        archive_format = "tar.gz"
    else:
        raise ValueError(f"Unsupported platform: {url_info.platform}")

    # Download archive to temporary file
    response = requests.get(archive_url, stream=True, timeout=60)
    response.raise_for_status()

    with tempfile.NamedTemporaryFile(
        delete=False, suffix=f".{archive_format}"
    ) as tmp_file:
        for chunk in response.iter_content(chunk_size=8192):
            tmp_file.write(chunk)
        tmp_path = tmp_file.name

    try:
        # Extract archive
        temp_extract_dir = Path(tempfile.mkdtemp())

        if archive_format == "zip":
            with zipfile.ZipFile(tmp_path, "r") as zip_ref:
                zip_ref.extractall(temp_extract_dir)
        else:  # tar.gz
            with tarfile.open(tmp_path, "r:gz") as tar_ref:
                tar_ref.extractall(temp_extract_dir)

        # Find the extracted directory (usually has format repo-branch)
        extracted_items = list(temp_extract_dir.iterdir())
        if len(extracted_items) == 1 and extracted_items[0].is_dir():
            extracted_dir = extracted_items[0]
        else:
            extracted_dir = temp_extract_dir

        # Determine source directory based on whether path is specified
        if url_info.path:
            # For URLs with path, find the specific subdirectory
            source_dir = extracted_dir / url_info.path
            if not source_dir.exists():
                raise ValueError(f"Path '{url_info.path}' not found in archive")
        else:
            # For URLs without path, use the root of the extracted archive
            source_dir = extracted_dir

        # Create destination and copy contents
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Copy all contents from source_dir to dest_dir
        for item in source_dir.iterdir():
            if item.is_dir():
                shutil.copytree(item, dest_dir / item.name)
            else:
                shutil.copy2(item, dest_dir / item.name)

        # Cleanup
        shutil.rmtree(temp_extract_dir)
    finally:
        # Remove temporary archive file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def _get_heptapod_vcs_type(url_info: UrlInfo) -> str:
    """
    Determine if a Heptapod project uses Git or Mercurial.

    Args:
        url_info: Repository information

    Returns:
        'git' or 'hg'
    """
    # Query the Heptapod/GitLab API to get project info
    project_id = f"{url_info.owner}%2F{url_info.repo}"
    api_url = f"{url_info.base_url}/api/v4/projects/{project_id}"
    response = requests.get(api_url, timeout=10)
    response.raise_for_status()
    project_info = response.json()
    return project_info.get("vcs_type")


def download_via_clone(url_info: UrlInfo, dest_dir: Path):
    """
    Download repository using git or hg clone.
    Only works when url_info.path is empty (full repo clone).

    Args:
        url_info: Repository information
        dest_dir: Destination directory
        shallow: Use shallow clone (depth=1)
    """
    if url_info.path:
        raise ValueError("Clone only supported for full repository (no path specified)")

    if url_info.platform == "heptapod":
        vcs = _get_heptapod_vcs_type(url_info)
    else:
        vcs = "git"

    clone_url = f"{url_info.base_url}/{url_info.owner}/{url_info.repo}"
    if vcs == "git":
        clone_url += ".git"
        clone_cmd = ["git", "clone", "--depth", "1", "--branch", url_info.ref]
        clone_cmd.extend([clone_url, str(dest_dir)])
    elif vcs == "hg":
        clone_cmd = ["hg", "clone"]
        if url_info.ref:
            if "/" in url_info.ref:
                # branch/default or topic/default/topic-name
                ref = url_info.ref.rsplit("/", maxsplit=1)[1]
            else:
                ref = url_info.ref
            clone_cmd.extend(["--rev", ref])
        clone_cmd.extend([clone_url, str(dest_dir)])
    else:
        raise ValueError(f"Unsupported VCS type: {vcs}")

    subprocess.run(clone_cmd, check=True)


def download_file_per_file(url_info: UrlInfo, dest_dir: Path) -> None:
    """
    Download repository files using platform API (without git/hg).
    For full repository (no path), downloads archive.
    For specific path, downloads files recursively.

    Args:
        url_info: Repository information
        dest_dir: Destination directory
    """
    dest_dir.mkdir(parents=True, exist_ok=True)

    if url_info.platform == "github":
        _download_github(url_info, dest_dir)
    elif url_info.platform in ("gitlab", "heptapod"):
        _download_gitlab(url_info, dest_dir)
    else:
        raise ValueError(f"Unsupported platform: {url_info.platform}")


def _download_github(url_info: UrlInfo, dest_dir: Path) -> None:
    """Download from GitHub API."""
    api_base = f"https://api.github.com/repos/{url_info.owner}/{url_info.repo}/contents"
    api_url = f"{api_base}/{url_info.path}" if url_info.path else api_base
    params = {"ref": url_info.ref} if url_info.ref else {}

    _download_github_directory(api_url, dest_dir, params)


def _download_github_directory(api_url: str, dest_dir: Path, params: dict) -> None:
    """Recursively download directory contents from GitHub."""
    response = requests.get(api_url, params=params, timeout=30)
    response.raise_for_status()

    items = response.json()

    # Handle single file case
    if isinstance(items, dict) and "type" in items:
        items = [items]

    for item in items:
        item_type = item["type"]
        item_name = item["name"]
        local_path = dest_dir / item_name

        if item_type == "dir":
            local_path.mkdir(parents=True, exist_ok=True)
            sub_api_url = item["url"]
            _download_github_directory(sub_api_url, local_path, {})
        else:  # file
            download_url = item["download_url"]

            file_response = requests.get(download_url, timeout=30)
            file_response.raise_for_status()

            local_path.write_bytes(file_response.content)


def _download_gitlab(url_info: UrlInfo, dest_dir: Path) -> None:
    """
    Download from GitLab API (works for GitLab instances and Heptapod).

    Args:
        url_info: Repository information
        dest_dir: Destination directory
    """
    base_url = url_info.base_url
    project_id = f"{url_info.owner}%2F{url_info.repo}"
    api_url = f"{base_url}/api/v4/projects/{project_id}/repository/tree"

    params: dict[str, Any] = {"recursive": True}
    if url_info.ref:
        params["ref"] = url_info.ref
    if url_info.path:
        params["path"] = url_info.path

    response = requests.get(api_url, params=params, timeout=30)
    response.raise_for_status()

    items = response.json()

    for item in items:
        item_type = item["type"]
        item_path = item["path"]

        # Remove base path prefix if downloading subdirectory
        if url_info.path:
            if not item_path.startswith(url_info.path):
                continue
            rel_path = item_path[len(url_info.path) :].lstrip("/")
        else:
            rel_path = item_path

        local_path = dest_dir / rel_path

        if item_type == "tree":
            local_path.mkdir(parents=True, exist_ok=True)
        else:  # blob (file)
            # Ensure parent directory exists
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Download file
            file_path_encoded = item_path.replace("/", "%2F")
            download_url = f"{base_url}/api/v4/projects/{project_id}/repository/files/{file_path_encoded}/raw"
            download_params = {"ref": url_info.ref} if url_info.ref else {}

            file_response = requests.get(
                download_url, params=download_params, timeout=30
            )
            file_response.raise_for_status()

            local_path.write_bytes(file_response.content)


def download_repo_files(
    url_info: UrlInfo,
    dest_dir: Path,
    method: Literal["auto", "clone", "archive", "file-per-file"] | None = None,
) -> Path:
    """
    Download files from a repository.

    Args:
        url_info: Repository URL information
        dest_dir: Destination directory (defaults to repo name or path basename)
        method: download method

    Returns:
        Path to the downloaded directory
    """
    if dest_dir.exists():
        raise FileExistsError(f"Error: {dest_dir} already exists.")

    # If no path specified, download archive for efficiency
    if method is None or method == "auto":
        # TODO: better guess
        if url_info.path:
            method = "file-per-file"
        else:
            method = "archive"

    if method == "clone":
        if url_info.path:
            raise ValueError(
                "clone_repo=True only supported for full repository downloads. "
                "URL must not contain a path component. "
                "Use clone_repo=False to download specific directories via API."
            )
        download_via_clone(url_info, dest_dir)
    elif method == "archive":
        download_via_archive(url_info, dest_dir)
    elif method == "file-per-file":
        download_file_per_file(url_info, dest_dir)
    else:
        raise ValueError(
            'method has to be in ["auto", "clone", "archive", "file-per-file"]'
        )
    return dest_dir
