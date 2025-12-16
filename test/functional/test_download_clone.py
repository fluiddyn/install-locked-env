import pytest

from install_locked_env.downloaders import download_via_clone

from .util import get_url_info_env


@pytest.mark.slow
@pytest.mark.parametrize("platform", ["github", "heptapod"])
def test_download_via_clone(tmp_path, platform):
    """test download via archives"""
    url_info = get_url_info_env(platform, "root")
    download_via_clone(url_info, tmp_path)

    dirs = ["src", "envs", "tools", "src", "docker"]
    for name in dirs:
        assert (tmp_path / name).is_dir()

    files = [
        "CHANGELOG.md",
        "Makefile",
        "pylock.toml",
        "README.md",
        "CONTRIBUTING.md",
        "LICENSE.txt",
        "pdm.toml",
        "pyproject.toml",
    ]
    for name in files:
        assert (tmp_path / name).is_file()
