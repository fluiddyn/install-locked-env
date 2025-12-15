import pytest

from install_locked_env.downloaders import _get_heptapod_vcs_type

from .util import get_url_info_env


@pytest.mark.slow
def test_vcs_type_repo_usr():
    """test _get_heptapod_vcs_type for repo url"""
    url_info = get_url_info_env("heptapod", "root")
    assert _get_heptapod_vcs_type(url_info) == "hg"


@pytest.mark.slow
def test_vcs_type_path():
    """test _get_heptapod_vcs_type for url with path"""
    url_info = get_url_info_env("heptapod", "pdm-pylock")
    assert _get_heptapod_vcs_type(url_info) == "hg"
