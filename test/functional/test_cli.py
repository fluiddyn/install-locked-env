from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from install_locked_env import app

from .util import get_url_env

runner = CliRunner()


@pytest.mark.slow
@pytest.mark.parametrize("platform", ["github", "heptapod"])
def test_app(tmp_path, platform):
    url = get_url_env(platform, "pdm-pylock")

    mock_env = Mock()
    mock_env.get_relative_path_log_file = Mock(return_value=["???"])
    mock_env.tool_name = "pdm"
    mock_env.tool_name = "env-pdm-pylock"
    mock_env.install = Mock()
    mock_env.register_jupyter_kernel = Mock()

    with patch(
        "install_locked_env.__main__.create_env_object",
        return_value=mock_env,
    ):
        result = runner.invoke(app, [url, "-o", str(tmp_path)])

    assert result.exit_code == 0

    assert "Repository: fluiddyn/install-locked-env" in result.output
    assert "Environment type: uv-pylock-pdm" in result.output
    assert f"Saved files to {tmp_path}" in result.output

    paths = set(path.name for path in tmp_path.glob("*"))
    assert "pdm.toml" in paths
    assert "pylock.toml" in paths
    assert "pyproject.toml" in paths
