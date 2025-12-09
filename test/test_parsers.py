"""Tests for URL parsing."""

import pytest
from install_locked_env.parsers import parse_url, UrlInfo, _split_ref_and_path


def test_split_ref_and_path_with_env_pattern():
    """Test splitting when path contains environment pattern."""
    ref, path = _split_ref_and_path("branch/default/pixi-envs/env-fluidsim")
    assert ref == "branch/default"
    assert path == "pixi-envs/env-fluidsim"


def test_split_ref_and_path_topic_branch():
    """Test splitting with topic branch."""
    ref, path = _split_ref_and_path("topic/default/feature-name/envs/dev")
    assert ref == "topic/default/feature-name"
    assert path == "envs/dev"


def test_split_ref_and_path_single_segment():
    """Test splitting with single segment (ref only)."""
    ref, path = _split_ref_and_path("main")
    assert ref == "main"
    assert path == ""


def test_split_ref_and_path_no_pattern():
    """Test splitting when no environment pattern found."""
    ref, path = _split_ref_and_path("branch/default/some-dir")
    assert ref == "branch/default"
    assert path == "some-dir"


def test_split_ref_and_path_empty():
    """Test splitting empty string."""
    ref, path = _split_ref_and_path("")
    assert ref == ""
    assert path == ""


def test_parse_github_url():
    """Test parsing a GitHub URL."""
    url = "https://github.com/fluiddyn/fluidsim/tree/5266c974e3368d17819f59b0e700b723591e0d1a/pixi-envs/env-fluidsim-mpi"

    result = parse_url(url)

    assert result.platform == "github"
    assert result.owner == "fluiddyn"
    assert result.repo == "fluidsim"
    assert result.ref == "5266c974e3368d17819f59b0e700b723591e0d1a"
    assert result.path == "pixi-envs/env-fluidsim-mpi"
    assert "raw.githubusercontent.com" in result.raw_url_template


def test_parse_github_url_with_branch():
    """Test parsing a GitHub URL with branch name."""
    url = "https://github.com/user/repo/tree/main/subdir"

    result = parse_url(url)

    assert result.platform == "github"
    assert result.ref == "main"
    assert result.path == "subdir"


def test_parse_github_url_with_slashed_branch():
    """Test parsing a GitHub URL with slashes in branch name."""
    url = "https://github.com/user/repo/tree/branch/feature-name/envs/dev"

    result = parse_url(url)

    assert result.platform == "github"
    assert result.ref == "branch/feature-name"
    assert result.path == "envs/dev"


def test_parse_heptapod_url():
    """Test parsing a Heptapod URL."""
    url = "https://foss.heptapod.net/fluiddyn/fluidsim/-/tree/branch/default/pixi-envs/env-fluidsim"

    result = parse_url(url)

    assert result.platform == "heptapod"
    assert result.owner == "fluiddyn"
    assert result.repo == "fluidsim"
    assert result.ref == "branch/default"
    assert result.path == "pixi-envs/env-fluidsim"
    assert "foss.heptapod.net" in result.raw_url_template


def test_parse_heptapod_url_topic_branch():
    """Test parsing a Heptapod URL with topic branch."""
    url = "https://foss.heptapod.net/user/repo/-/tree/topic/default/feature/envs/test"

    result = parse_url(url)

    assert result.platform == "heptapod"
    assert result.ref == "topic/default/feature"
    assert result.path == "envs/test"


def test_parse_gitlab_url():
    """Test parsing a GitLab URL."""
    url = "https://gitlab.com/user/project/-/tree/main/envs/dev"

    result = parse_url(url)

    assert result.platform == "gitlab"
    assert result.owner == "user"
    assert result.repo == "project"
    assert result.ref == "main"
    assert result.path == "envs/dev"


def test_parse_gitlab_url_with_slashed_branch():
    """Test parsing a GitLab URL with slashes in branch."""
    url = "https://gitlab.com/user/project/-/tree/release/v1.0/pixi-envs/prod"

    result = parse_url(url)

    assert result.platform == "gitlab"
    assert result.ref == "release/v1.0"
    assert result.path == "pixi-envs/prod"


def test_parse_invalid_github_url():
    """Test that invalid GitHub URLs raise ValueError."""
    with pytest.raises(ValueError, match="Invalid GitHub URL format"):
        parse_url("https://github.com/user/repo")


def test_parse_invalid_gitlab_url():
    """Test that invalid GitLab URLs raise ValueError."""
    with pytest.raises(ValueError, match="Invalid gitlab URL format"):
        parse_url("https://gitlab.com/user/repo/tree/main")


def test_parse_unsupported_platform():
    """Test that unsupported platforms raise ValueError."""
    with pytest.raises(ValueError, match="Unsupported platform"):
        parse_url("https://bitbucket.org/user/repo")


def test_github_raw_url_template():
    """Test that GitHub raw URL template is correctly formatted."""
    url = "https://github.com/user/repo/tree/main/path/to/env"
    result = parse_url(url)

    raw_url = result.raw_url_template.format(filename="pixi.toml")
    assert (
        raw_url
        == "https://raw.githubusercontent.com/user/repo/main/path/to/env/pixi.toml"
    )


def test_github_raw_url_template_slashed_ref():
    """Test GitHub raw URL with slashed ref."""
    url = "https://github.com/user/repo/tree/feature/branch-name/envs/test"
    result = parse_url(url)

    raw_url = result.raw_url_template.format(filename="pixi.toml")
    assert (
        raw_url
        == "https://raw.githubusercontent.com/user/repo/feature/branch-name/envs/test/pixi.toml"
    )


def test_gitlab_raw_url_template():
    """Test that GitLab raw URL template is correctly formatted."""
    url = "https://gitlab.com/user/repo/-/tree/main/path"
    result = parse_url(url)

    raw_url = result.raw_url_template.format(filename="pixi.lock")
    assert raw_url == "https://gitlab.com/user/repo/-/raw/main/path/pixi.lock"


def test_heptapod_raw_url_template_slashed_ref():
    """Test Heptapod raw URL with slashed ref."""
    url = "https://foss.heptapod.net/user/repo/-/tree/branch/default/envs/dev"
    result = parse_url(url)

    raw_url = result.raw_url_template.format(filename="pixi.lock")
    assert (
        raw_url
        == "https://foss.heptapod.net/user/repo/-/raw/branch/default/envs/dev/pixi.lock"
    )
