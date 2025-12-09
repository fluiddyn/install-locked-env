"""File downloading utilities."""

import httpx
from .parsers import UrlInfo


PIXI_FILES = ["pixi.toml", "pixi.lock"]
UV_FILES = ["pyproject.toml", "uv.lock"]
PDM_FILES = ["pyproject.toml", "pdm.lock"]
POETRY_FILES = ["pyproject.toml", "poetry.lock"]


def download_files(url_info: UrlInfo) -> dict[str, str]:
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
        # Try pixi first (as per the prototype requirement)
        for filename in PIXI_FILES:
            try:
                url = url_info.raw_url_template.format(filename=filename)
                response = client.get(url)
                response.raise_for_status()
                files[filename] = response.text
            except httpx.HTTPStatusError:
                # File doesn't exist, try next
                continue

        if files:
            return files

        # If no pixi files, try other formats (for future expansion)
        for filenames in [UV_FILES, PDM_FILES, POETRY_FILES]:
            for filename in filenames:
                try:
                    url = url_info.raw_url_template.format(filename=filename)
                    response = client.get(url)
                    response.raise_for_status()
                    files[filename] = response.text
                except httpx.HTTPStatusError:
                    continue
            if files:
                return files

    if not files:
        raise ValueError(
            f"No supported lock files found at {url_info.path}. "
            "Looked for: pixi.toml/pixi.lock, pyproject.toml/uv.lock, "
            "pyproject.toml/pdm.lock, pyproject.toml/poetry.lock"
        )

    return files
