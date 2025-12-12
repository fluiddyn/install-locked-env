"""Test suite for environment management classes."""

from pathlib import Path
from unittest.mock import Mock, patch, mock_open, ANY
import pytest

from install_locked_env.environments import (
    Environment,
    PixiEnvironment,
    UvPylockEnvironment,
    UvEnvironment,
    PdmEnvironment,
)


# Fixtures
@pytest.fixture
def temp_env_dir(tmp_path):
    """Create a temporary environment directory."""
    env_dir = tmp_path / "test_env"
    env_dir.mkdir()
    return env_dir


@pytest.fixture
def pixi_toml_content():
    """Sample pixi.toml content."""
    return b"""
[project]
name = "test-project"
version = "0.1.0"
"""


@pytest.fixture
def pyproject_toml_content():
    """Sample pyproject.toml content."""
    return b"""
[project]
name = "test-project"
version = "0.1.0"
"""


# Base Environment Tests
class TestEnvironment:
    """Tests for the base Environment class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that Environment cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Environment(Path("/tmp"))

    def test_check_tool_raises_when_tool_missing(self, temp_env_dir):
        """Test that _check_tool raises FileNotFoundError when tool is missing."""

        class TestEnv(Environment):
            tool_name = "nonexistent_tool_xyz"
            _tool_install_url = "https://example.com"

            def _detect_name(self):
                return "test"

            def install(self):
                pass

            def run_in_env(self, command, **kwargs):
                pass

            def _has_ipykernel(self):
                return False

        with pytest.raises(
            FileNotFoundError, match="nonexistent_tool_xyz is not installed"
        ):
            TestEnv(temp_env_dir)

    def test_name_property_caching(self, temp_env_dir):
        """Test that name property caches the detected name."""

        class TestEnv(Environment):
            tool_name = None

            def _detect_name(self):
                return "detected-name"

            def install(self):
                pass

            def run_in_env(self, command, **kwargs):
                pass

            def _has_ipykernel(self):
                return False

        env = TestEnv(temp_env_dir)
        # First access should detect
        name1 = env.name
        # Second access should use cached value
        name2 = env.name
        assert name1 == name2 == "detected-name"

    def test_venv_path_created_when_venv_dir_set(self, temp_env_dir):
        """Test that venv_path is set when _venv_dir is provided."""

        class TestEnv(Environment):
            tool_name = None
            _venv_dir = ".venv"

            def _detect_name(self):
                return "test"

            def install(self):
                pass

            def run_in_env(self, command, **kwargs):
                pass

            def _has_ipykernel(self):
                return False

        env = TestEnv(temp_env_dir)
        assert hasattr(env, "venv_path")
        assert env.venv_path == temp_env_dir / ".venv"


# PixiEnvironment Tests
class TestPixiEnvironment:
    """Tests for PixiEnvironment."""

    @patch("shutil.which")
    def test_init_raises_when_pixi_not_installed(self, mock_which, temp_env_dir):
        """Test that initialization fails when pixi is not installed."""
        mock_which.return_value = None

        with pytest.raises(FileNotFoundError, match="pixi is not installed"):
            PixiEnvironment(temp_env_dir)

    @patch("shutil.which")
    @patch("builtins.open", new_callable=mock_open)
    @patch("tomllib.load")
    def test_detect_name_from_pixi_toml(
        self, mock_toml_load, mock_file, mock_which, temp_env_dir, pixi_toml_content
    ):
        """Test name detection from pixi.toml."""
        mock_which.return_value = "/usr/bin/pixi"
        mock_toml_load.return_value = {"project": {"name": "my-pixi-project"}}

        env = PixiEnvironment(temp_env_dir)
        assert env.name == "my-pixi-project"

    @patch("shutil.which")
    @patch("builtins.open", new_callable=mock_open)
    @patch("tomllib.load")
    def test_detect_name_fallback_to_dir_name(
        self, mock_toml_load, mock_file, mock_which, temp_env_dir
    ):
        """Test that directory name is used when project name is missing."""
        mock_which.return_value = "/usr/bin/pixi"
        mock_toml_load.return_value = {}

        env = PixiEnvironment(temp_env_dir)
        assert env.name == temp_env_dir.name

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_install(self, mock_run, mock_which, temp_env_dir):
        """Test pixi environment installation."""
        mock_which.return_value = "/usr/bin/pixi"
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        env = PixiEnvironment(temp_env_dir, name="test-env")
        env.install()

        mock_run.assert_called_once_with(
            ["pixi", "install"],
            cwd=temp_env_dir,
            capture_output=True,
            text=True,
            check=True,
            env=ANY,
        )

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_run_in_env(self, mock_run, mock_which, temp_env_dir):
        """Test running command in pixi environment."""
        mock_which.return_value = "/usr/bin/pixi"
        mock_run.return_value = Mock(returncode=0, stdout="output", stderr="")

        env = PixiEnvironment(temp_env_dir, name="test-env")
        result = env.run_in_env(["python", "script.py"])

        mock_run.assert_called_once_with(
            ["pixi", "run", "python", "script.py"],
            cwd=temp_env_dir,
            capture_output=True,
            text=True,
            check=True,
            env=ANY,
        )
        assert result.stdout == "output"

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_has_ipykernel_true(self, mock_run, mock_which, temp_env_dir):
        """Test ipykernel detection when present."""
        mock_which.return_value = "/usr/bin/pixi"
        mock_run.return_value = Mock(returncode=0, stdout="ipykernel 6.0.0", stderr="")

        env = PixiEnvironment(temp_env_dir, name="test-env")
        assert env._has_ipykernel() is True

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_has_ipykernel_false(self, mock_run, mock_which, temp_env_dir):
        """Test ipykernel detection when absent."""
        mock_which.return_value = "/usr/bin/pixi"
        mock_run.return_value = Mock(returncode=0, stdout="numpy 1.0.0", stderr="")

        env = PixiEnvironment(temp_env_dir, name="test-env")
        assert env._has_ipykernel() is False

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_register_jupyter_kernel_success(self, mock_run, mock_which, temp_env_dir):
        """Test successful Jupyter kernel registration."""
        mock_which.return_value = "/usr/bin/pixi"
        # First call for _has_ipykernel, second for registration
        mock_run.side_effect = [
            Mock(returncode=0, stdout="ipykernel 6.0.0", stderr=""),
            Mock(returncode=0, stdout="", stderr=""),
        ]

        env = PixiEnvironment(temp_env_dir, name="test-env")
        result = env.register_jupyter_kernel()

        assert result is True
        assert mock_run.call_count == 2

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_register_jupyter_kernel_no_ipykernel(
        self, mock_run, mock_which, temp_env_dir
    ):
        """Test kernel registration fails when ipykernel is missing."""
        mock_which.return_value = "/usr/bin/pixi"
        mock_run.return_value = Mock(returncode=0, stdout="numpy 1.0.0", stderr="")

        env = PixiEnvironment(temp_env_dir, name="test-env")
        result = env.register_jupyter_kernel()

        assert result is False

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_list_packages(self, mock_run, mock_which, temp_env_dir):
        """Test listing packages in pixi environment."""
        mock_which.return_value = "/usr/bin/pixi"
        mock_run.return_value = Mock(
            returncode=0, stdout="numpy 1.0.0\nscipy 2.0.0\nipykernel 6.0.0", stderr=""
        )

        env = PixiEnvironment(temp_env_dir, name="test-env")
        packages = env.list_packages()

        assert "numpy" in packages
        assert "scipy" in packages
        assert "ipykernel" in packages


# UvPylockEnvironment Tests
class TestUvPylockEnvironment:
    """Tests for UvPylockEnvironment."""

    @patch("shutil.which")
    def test_init_raises_when_uv_not_installed(self, mock_which, temp_env_dir):
        """Test that initialization fails when uv is not installed."""
        mock_which.return_value = None

        with pytest.raises(FileNotFoundError, match="uv is not installed"):
            UvPylockEnvironment(temp_env_dir)

    @patch("shutil.which")
    def test_venv_path_set(self, mock_which, temp_env_dir):
        """Test that venv_path is set correctly."""
        mock_which.return_value = "/usr/bin/uv"

        env = UvPylockEnvironment(temp_env_dir, name="test-env")
        assert env.venv_path == temp_env_dir / ".venv"

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_install_creates_venv_and_syncs(self, mock_run, mock_which, temp_env_dir):
        """Test installation creates venv and syncs dependencies."""
        mock_which.return_value = "/usr/bin/uv"
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        env = UvPylockEnvironment(temp_env_dir, name="test-env")
        env.install()

        # Should call uv venv and uv pip sync
        assert mock_run.call_count == 2


# UvEnvironment Tests
class TestUvEnvironment:
    """Tests for UvEnvironment."""

    @patch("shutil.which")
    def test_init_raises_when_uv_not_installed(self, mock_which, temp_env_dir):
        """Test that initialization fails when uv is not installed."""
        mock_which.return_value = None

        with pytest.raises(FileNotFoundError, match="uv is not installed"):
            UvEnvironment(temp_env_dir)

    @patch("shutil.which")
    @patch("builtins.open", new_callable=mock_open)
    @patch("tomllib.load")
    def test_detect_name_from_pyproject_toml(
        self, mock_toml_load, mock_file, mock_which, temp_env_dir
    ):
        """Test name detection from pyproject.toml."""
        mock_which.return_value = "/usr/bin/uv"
        mock_toml_load.return_value = {"project": {"name": "my-uv-project"}}

        env = UvEnvironment(temp_env_dir)
        assert env.name == "my-uv-project"

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_install(self, mock_run, mock_which, temp_env_dir):
        """Test uv environment installation."""
        mock_which.return_value = "/usr/bin/uv"
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        env = UvEnvironment(temp_env_dir, name="test-env")
        env.install()

        mock_run.assert_called_once_with(
            ["uv", "sync"],
            cwd=temp_env_dir,
            capture_output=True,
            text=True,
            check=True,
            env=ANY,
        )

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_run_in_env(self, mock_run, mock_which, temp_env_dir):
        """Test running command in uv environment."""
        mock_which.return_value = "/usr/bin/uv"
        mock_run.return_value = Mock(returncode=0, stdout="test output", stderr="")

        env = UvEnvironment(temp_env_dir, name="test-env")
        result = env.run_in_env(["pytest"])

        mock_run.assert_called_once_with(
            ["uv", "run", "pytest"],
            cwd=temp_env_dir,
            capture_output=True,
            text=True,
            check=True,
            env=ANY,
        )
        assert result.stdout == "test output"


# PdmEnvironment Tests
class TestPdmEnvironment:
    """Tests for PdmEnvironment."""

    @patch("shutil.which")
    def test_init_raises_when_pdm_not_installed(self, mock_which, temp_env_dir):
        """Test that initialization fails when pdm is not installed."""
        mock_which.return_value = None

        with pytest.raises(FileNotFoundError, match="pdm is not installed"):
            PdmEnvironment(temp_env_dir)

    @patch("shutil.which")
    @patch("builtins.open", new_callable=mock_open)
    @patch("tomllib.load")
    def test_detect_name_from_pyproject_toml(
        self, mock_toml_load, mock_file, mock_which, temp_env_dir
    ):
        """Test name detection from pyproject.toml."""
        mock_which.return_value = "/usr/bin/pdm"
        mock_toml_load.return_value = {"project": {"name": "my-pdm-project"}}

        env = PdmEnvironment(temp_env_dir)
        assert env.name == "my-pdm-project"

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_install(self, mock_run, mock_which, temp_env_dir):
        """Test pdm environment installation."""
        mock_which.return_value = "/usr/bin/pdm"
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        env = PdmEnvironment(temp_env_dir, name="test-env")
        env.install()

        mock_run.assert_called_once_with(
            ["pdm", "sync"],
            cwd=temp_env_dir,
            capture_output=True,
            text=True,
            check=True,
            env=ANY,
        )

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_run_in_env(self, mock_run, mock_which, temp_env_dir):
        """Test running command in pdm environment."""
        mock_which.return_value = "/usr/bin/pdm"
        mock_run.return_value = Mock(returncode=0, stdout="pdm output", stderr="")

        env = PdmEnvironment(temp_env_dir, name="test-env")
        result = env.run_in_env(["python", "-m", "pytest"])

        mock_run.assert_called_once_with(
            ["pdm", "run", "python", "-m", "pytest"],
            cwd=temp_env_dir,
            capture_output=True,
            text=True,
            check=True,
            env=ANY,
        )
        assert result.stdout == "pdm output"

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_has_ipykernel(self, mock_run, mock_which, temp_env_dir):
        """Test ipykernel detection in pdm environment."""
        mock_which.return_value = "/usr/bin/pdm"
        mock_run.return_value = Mock(returncode=0, stdout="ipykernel 6.0.0", stderr="")

        env = PdmEnvironment(temp_env_dir, name="test-env")
        assert env._has_ipykernel() is True


# Integration-style Tests
class TestEnvironmentIntegration:
    """Integration tests for common scenarios."""

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_full_workflow_pixi(self, mock_run, mock_which, temp_env_dir):
        """Test full workflow: create, install, register kernel."""
        mock_which.return_value = "/usr/bin/pixi"
        mock_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # install
            Mock(returncode=0, stdout="ipykernel 6.0.0", stderr=""),  # check ipykernel
            Mock(returncode=0, stdout="", stderr=""),  # register kernel
        ]

        env = PixiEnvironment(temp_env_dir, name="integration-test")
        env.install()
        success = env.register_jupyter_kernel()

        assert success is True
        assert mock_run.call_count == 3

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_run_with_custom_kwargs(self, mock_run, mock_which, temp_env_dir):
        """Test that custom kwargs are passed through to subprocess.run."""
        mock_which.return_value = "/usr/bin/uv"
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        env = UvEnvironment(temp_env_dir, name="test-env")
        env.run_in_env(["python", "script.py"], check=False, timeout=30)

        # Verify custom kwargs were passed
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["check"] is False
        assert call_kwargs["timeout"] == 30
