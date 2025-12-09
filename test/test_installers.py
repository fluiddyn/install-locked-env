"""Tests for environment installation."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import subprocess
from install_locked_env.installers import install_pixi_env, register_jupyter_kernel


@pytest.fixture
def temp_env_dir(tmp_path):
    """Create a temporary environment directory with pixi.toml."""
    env_dir = tmp_path / "test-env"
    env_dir.mkdir()

    pixi_toml = env_dir / "pixi.toml"
    pixi_toml.write_text("""
[project]
name = "test-env"
version = "0.1.0"
""")

    return env_dir


def test_install_pixi_env_pixi_not_found(temp_env_dir):
    """Test error when pixi is not installed."""
    with patch("shutil.which", return_value=None):
        with pytest.raises(FileNotFoundError, match="pixi is not installed"):
            install_pixi_env(temp_env_dir)


def test_install_pixi_env_success(temp_env_dir):
    """Test successful pixi environment installation."""
    with patch("shutil.which", return_value="/usr/bin/pixi"):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            env_name = install_pixi_env(temp_env_dir)

            assert env_name == "test-env"
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args[0][0] == ["pixi", "install"]
            assert call_args[1]["cwd"] == temp_env_dir


def test_install_pixi_env_subprocess_error(temp_env_dir):
    """Test error handling when pixi install fails."""
    with patch("shutil.which", return_value="/usr/bin/pixi"):
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, ["pixi", "install"])

            with pytest.raises(subprocess.CalledProcessError):
                install_pixi_env(temp_env_dir)


def test_install_pixi_env_fallback_name(tmp_path):
    """Test that directory name is used when project.name is not in pixi.toml."""
    env_dir = tmp_path / "fallback-env"
    env_dir.mkdir()

    pixi_toml = env_dir / "pixi.toml"
    pixi_toml.write_text("[dependencies]\n")

    with patch("shutil.which", return_value="/usr/bin/pixi"):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            env_name = install_pixi_env(env_dir)

            assert env_name == "fallback-env"


def test_register_jupyter_kernel_no_ipykernel(temp_env_dir):
    """Test that kernel registration returns False when ipykernel is not found."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(
            returncode=0, stdout="numpy\npandas\nscipy\n", stderr=""
        )

        result = register_jupyter_kernel(temp_env_dir, "test-env")

        assert result is False


def test_register_jupyter_kernel_success(temp_env_dir):
    """Test successful kernel registration when ipykernel is present."""
    with patch("subprocess.run") as mock_run:
        # First call: pixi list shows ipykernel
        # Second call: kernel registration
        mock_run.side_effect = [
            Mock(returncode=0, stdout="ipykernel\nnumpy\npandas\n", stderr=""),
            Mock(returncode=0, stdout="", stderr=""),
        ]

        result = register_jupyter_kernel(temp_env_dir, "test-env")

        assert result is True
        assert mock_run.call_count == 2

        # Check the kernel registration command
        kernel_call = mock_run.call_args_list[1]
        assert "ipykernel" in kernel_call[0][0]
        assert "--name" in kernel_call[0][0]
        assert "test-env" in kernel_call[0][0]


def test_register_jupyter_kernel_registration_fails(temp_env_dir):
    """Test that registration failure returns False."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            Mock(returncode=0, stdout="ipykernel\n", stderr=""),
            subprocess.CalledProcessError(1, ["pixi", "run"]),
        ]

        result = register_jupyter_kernel(temp_env_dir, "test-env")

        assert result is False
