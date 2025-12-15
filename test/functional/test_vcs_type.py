import pytest

from install_locked_env.parsers import UrlInfo
from install_locked_env.downloaders import _get_heptapod_vcs_type


@pytest.mark.slow
def test_vcs_type_py_edu_fr():
    url_info = UrlInfo.from_url("https://foss.heptapod.net/py-edu-fr/py-edu-fr")
    assert _get_heptapod_vcs_type(url_info) == "hg"


@pytest.mark.slow
def test_vcs_type_install_locked_file():
    url_info = UrlInfo.from_url(
        "https://foss.heptapod.net/fluiddyn/install-locked-env/-/tree/branch/default/envs/env-pdm-pylock"
    )
    assert _get_heptapod_vcs_type(url_info) == "hg"
