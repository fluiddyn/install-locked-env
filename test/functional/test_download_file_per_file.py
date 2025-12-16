import pytest


from install_locked_env.downloaders import download_file_per_file

from .util import get_url_info_env


@pytest.mark.slow
@pytest.mark.parametrize("platform", ["github", "heptapod"])
def test_download_file_per_file(tmp_path, platform):
    """test download file per file"""
    url_info = get_url_info_env(platform, "pdm-pylock")
    download_file_per_file(url_info, tmp_path)
    paths = set(path.name for path in tmp_path.glob("*"))
    assert "pdm.toml" in paths
    assert "pylock.toml" in paths
    assert "pyproject.toml" in paths
