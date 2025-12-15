import pytest


from install_locked_env.downloaders import download_via_archive

from .util import get_url_info_env


@pytest.mark.slow
@pytest.mark.parametrize("platform", ["github", "heptapod"])
def test_download_archive(tmp_path, platform):
    """test download via archives"""
    url_info = get_url_info_env(platform, "pixi-skimage")
    download_via_archive(url_info, tmp_path)
    paths = set(path.name for path in tmp_path.glob("*"))
    assert "pixi.toml" in paths
    assert "pixi.lock" in paths
    assert "README.md" in paths
    assert "Makefile" in paths
    assert [path for path in paths if path.endswith(".py")]
