import pytest

from install_locked_env.parsers import UrlInfo

from install_locked_env import downloaders


ref = "branch/default"
path = "envs/env-pixi-skimage"


@pytest.mark.slow
@pytest.mark.parametrize("netloc", ["github.com", "foss.heptapod.net"])
def test_download_archive(tmp_path, netloc):
    """test download via archives"""
    url = f"https://{netloc}/fluiddyn/install-locked-env"
    if not netloc.startswith("github"):
        url += "/-"
    url += f"/tree/{ref}/{path}"

    url_info = UrlInfo.from_url(url)
    downloaders.download_via_archive(url_info, tmp_path)
    paths = set(path.name for path in tmp_path.glob("*"))
    assert "pixi.toml" in paths
    assert "pixi.lock" in paths
    assert "README.md" in paths
    assert "Makefile" in paths
    assert [path for path in paths if path.endswith(".py")]
