from unittest.mock import Mock, patch

import pytest
import requests
from typer.testing import CliRunner

from install_locked_env import app

from .util import get_url_env

runner = CliRunner()

cases = [
    ("github", True),
    ("github", False),
    ("heptapod", True),
    ("heptapod", False),
]


@pytest.mark.slow
@pytest.mark.parametrize("platform, minimal", cases)
def test_app_simple(tmp_path, platform, minimal):
    url = get_url_env(platform, "pdm-pylock")

    tmp_path = tmp_path / "env_dir"

    mock_env = Mock()
    mock_env.get_relative_path_log_file = Mock(return_value=["???"])
    mock_env.tool_name = "pdm"
    mock_env.tool_name = "env-pdm-pylock"
    mock_env.install = Mock()
    mock_env.register_jupyter_kernel = Mock()

    options = [url, "-o", str(tmp_path)]
    if minimal:
        options.append("--minimal")

    with patch(
        "install_locked_env.__main__.create_env_object",
        return_value=mock_env,
    ):
        result = runner.invoke(app, options)

    exc = result.exception
    if (
        exc is not None
        and isinstance(exc, requests.exceptions.HTTPError)
        and exc.response.status_code == 403
    ):
        # Forbidden (typically rate limit exceeded GitHub API)
        pytest.skip("Skipping because of 403 HTTP error")

    assert result.exit_code == 0

    assert "Repository: fluiddyn/install-locked-env" in result.output
    assert "Environment type: uv-pylock-pdm" in result.output
    assert "Saved files to " in result.output

    paths = set(path.name for path in tmp_path.glob("*"))
    assert "pdm.toml" in paths
    assert "pylock.toml" in paths
    assert "pyproject.toml" in paths
