from install_locked_env.parsers import UrlInfo


def get_url_env(platform: str, kind: str) -> str:
    """Get url corresponding to a venv"""
    if platform == "github":
        netloc = "github.com"
    elif platform == "heptapod":
        netloc = "foss.heptapod.net"
    else:
        raise ValueError

    ref = "branch/default"

    url = f"https://{netloc}/fluiddyn/install-locked-env"
    if kind != "root":
        path = f"envs/env-{kind}"
        if not netloc.startswith("github"):
            url += "/-"
        url += f"/tree/{ref}/{path}"

    return url


def get_url_info_env(platform: str, kind: str) -> UrlInfo:
    """Create a UrlInfo corresponding to a venv"""

    return UrlInfo.from_url(get_url_env(platform, kind))
