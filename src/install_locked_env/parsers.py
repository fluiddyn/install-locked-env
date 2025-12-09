"""URL parsing utilities."""

from dataclasses import dataclass
from urllib.parse import urlparse
import re


@dataclass
class UrlInfo:
    """Information extracted from a repository URL."""

    platform: str  # github, gitlab, heptapod
    owner: str
    repo: str
    ref: str  # branch name or commit hash
    path: str  # path within the repository
    raw_url_template: str  # template for raw file URLs


def _split_ref_and_path(ref_and_path: str) -> tuple[str, str]:
    """Split a combined ref+path string into separate ref and path components.

    Since refs can contain slashes (e.g., "branch/default", "topic/feature/name"),
    we need a heuristic to determine where the ref ends and the path begins.

    Strategy:
    - Common path patterns for lock files: "*-envs/", "envs/", "environments/", "locks/", etc.
    - If we find these patterns, everything before is the ref
    - Otherwise, assume the last segment is the path and everything else is ref
    - If there's only one segment, it's the ref with no path

    Args:
        ref_and_path: Combined string like "branch/default/pixi-envs/env-name"

    Returns:
        Tuple of (ref, path)
    """
    if not ref_and_path:
        return "", ""

    parts = ref_and_path.split("/")

    if len(parts) == 1:
        # Just a ref, no path
        return ref_and_path, ""

    # Look for common environment directory patterns
    env_patterns = [
        "envs",
        "env",
        "environments",
        "pixi-envs",
        "locks",
        "lock-files",
        ".pixi",
        "conda-envs",
    ]

    for i, part in enumerate(parts):
        # Check if this part matches an environment directory pattern
        if any(pattern in part.lower() for pattern in env_patterns):
            # Everything before this is the ref
            ref = "/".join(parts[:i])
            path = "/".join(parts[i:])
            return ref, path

    # No pattern found - assume last segment is path, rest is ref
    # This handles cases like "main/subdir" or "branch/default/final-dir"
    ref = "/".join(parts[:-1])
    path = parts[-1]

    return ref, path


def parse_url(url: str) -> UrlInfo:
    """Parse a repository URL and extract relevant information.

    Args:
        url: URL to a repository directory

    Returns:
        UrlInfo object with extracted information

    Raises:
        ValueError: If URL format is not recognized
    """
    parsed = urlparse(url)

    if "github.com" in parsed.netloc:
        return _parse_github_url(url, parsed)
    elif "gitlab" in parsed.netloc or "heptapod" in parsed.netloc:
        return _parse_gitlab_url(url, parsed)
    else:
        raise ValueError(f"Unsupported platform: {parsed.netloc}")


def _parse_github_url(url: str, parsed) -> UrlInfo:
    """Parse a GitHub URL.

    Expected format: https://github.com/{owner}/{repo}/tree/{ref}/{path}
    Note: {ref} can contain slashes (e.g., "branch/default", "topic/feature/name")
    """
    path_parts = parsed.path.strip("/").split("/")

    if len(path_parts) < 4 or path_parts[2] != "tree":
        raise ValueError(
            "Invalid GitHub URL format. Expected: "
            "https://github.com/{owner}/{repo}/tree/{ref}/{path}"
        )

    owner = path_parts[0]
    repo = path_parts[1]
    # Everything after /tree/ until we can identify the repo path
    # We need to reconstruct the full ref + path, then split them
    after_tree = "/".join(path_parts[3:])

    # Strategy: Try to identify where the ref ends and the path begins
    # We'll use the URL to fetch and test, but for now we need a heuristic
    # The ref is everything up to the last identifiable path component
    # For the template, we'll include the full after_tree and let the user structure work
    ref, repo_path = _split_ref_and_path(after_tree)

    return UrlInfo(
        platform="github",
        owner=owner,
        repo=repo,
        ref=ref,
        path=repo_path,
        raw_url_template=f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{repo_path}/{{filename}}",
    )


def _parse_gitlab_url(url: str, parsed) -> UrlInfo:
    """Parse a GitLab/Heptapod URL.

    Expected formats:
    - https://gitlab.com/{owner}/{repo}/-/tree/{ref}/{path}
    - https://foss.heptapod.net/{owner}/{repo}/-/tree/{ref}/{path}

    Note: {ref} can contain slashes (e.g., "branch/default", "topic/feature/name")
    """
    platform = "heptapod" if "heptapod" in parsed.netloc else "gitlab"

    # GitLab/Heptapod URLs have /-/ separator
    # Split on /-/tree/ to separate the prefix from ref+path
    path_match = re.match(r"^/([^/]+)/([^/]+)/-/tree/(.+)$", parsed.path)

    if not path_match:
        raise ValueError(
            f"Invalid {platform} URL format. Expected: "
            f"https://{parsed.netloc}/{{owner}}/{{repo}}/-/tree/{{ref}}/{{path}}"
        )

    owner = path_match.group(1)
    repo = path_match.group(2)
    ref_and_path = path_match.group(3)

    # Split ref and path
    ref, repo_path = _split_ref_and_path(ref_and_path)

    # For GitLab/Heptapod, we need to URL-encode the ref for raw URLs
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    return UrlInfo(
        platform=platform,
        owner=owner,
        repo=repo,
        ref=ref,
        path=repo_path,
        raw_url_template=f"{base_url}/{owner}/{repo}/-/raw/{ref}/{repo_path}/{{filename}}",
    )
