"""File downloading utilities."""

import httpx
from .parsers import UrlInfo


tools_files = {
    "uv-pylock": ["pyproject.toml", "pylock.toml"],
    "uv-pylock-alone": ["pylock.toml"],
    "pixi": ["pixi.toml", "pixi.lock"],
    "uv": ["pyproject.toml", "uv.lock"],
    "pdm-uv": ["pyproject.toml", "pdm.lock", "pdm.toml"],
    "pdm": ["pyproject.toml", "pdm.lock"],
    "poetry": ["pyproject.toml", "poetry.lock"],
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
                return tool, files

        for_error = ", ".join("/".join(names) for names in tools_files.values())
        raise ValueError(
            f"No supported lock files found at {url_info.path}. Looked for: {for_error}"
        )
