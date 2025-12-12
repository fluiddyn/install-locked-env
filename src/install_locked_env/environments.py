"""Environment management classes."""

import os
import subprocess
import shlex
import shutil
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Optional
import tomllib


class Environment(ABC):
    """Base class for environment management.

    Args:
        env_dir: Directory containing the environment
        name: Optional name for the environment (auto-detected if not provided)
    """

    # Class attributes to be overridden by subclasses
    tool_name: Optional[str] = None
    _tool_install_url: Optional[str] = None
    _venv_dir: Optional[str] = None
    _install_cmd: Optional[str | list] = None
    _list_packages_cmd: Optional[str] = None

    def __init__(self, env_dir: Path, name: Optional[str] = None):
        self._check_tool()
        self.env_dir = Path(env_dir)
        self._name = name
        self.path_log_file = self.env_dir / "log_install.txt"
        if self._venv_dir:
            self.venv_path = self.env_dir / self._venv_dir

    @property
    def name(self) -> str:
        """Get the environment name."""
        if self._name is None:
            self._name = self._detect_name()
        return self._name

    def _check_tool(self) -> None:
        """Check if the required tool is installed and raise error with installation tip if not.

        Raises:
            FileNotFoundError: If the tool is not installed
        """
        if self.tool_name and not shutil.which(self.tool_name):
            raise FileNotFoundError(
                f"{self.tool_name} is not installed. Install it from {self._tool_install_url}"
            )

    @abstractmethod
    def _detect_name(self) -> str:
        """Detect the environment name from configuration."""

    def _run_in_dir(
        self, cmd, capture_output=True, check=True, log_file=None, **kwargs
    ):
        """run a subprocess in env_dir"""
        if isinstance(cmd, str):
            cmd = shlex.split(cmd)

        env = {
            key: value
            for key, value in os.environ.copy().items()
            if not key.startswith("VIRTUAL_ENV")
        }
        assert "VIRTUAL_ENV" not in env

        stdout = stderr = log_file
        if log_file is not None:
            capture_output = False

        return subprocess.run(
            cmd,
            cwd=self.env_dir,
            capture_output=capture_output,
            text=True,
            check=check,
            env=env,
            stdout=stdout,
            stderr=stderr,
            **kwargs,
        )

    def install(self) -> None:
        """Install the environment."""
        with open(self.path_log_file, "w", encoding="utf-8") as file:
            self._run_in_dir(self._install_cmd, log_file=file)

    def run_in_env(self, command: list[str], **kwargs) -> subprocess.CompletedProcess:
        """Run a command in the environment.

        Args:
            command: Command to run as a list of strings
            **kwargs: Additional arguments to pass to subprocess.run

        Returns:
            CompletedProcess object
        """
        return self._run_in_dir([self.tool_name, "run"] + command, **kwargs)

    def register_jupyter_kernel(self) -> bool:
        """Register the environment as a Jupyter kernel if ipykernel is present.

        Returns:
            True if kernel was registered, False if ipykernel not found
        """
        if not self._has_ipykernel():
            return False

        try:
            self.run_in_env(
                [
                    "python",
                    "-m",
                    "ipykernel",
                    "install",
                    "--user",
                    "--name",
                    self.name,
                    "--display-name",
                    f"Python ({self.name})",
                ],
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _has_ipykernel(self) -> bool:
        """Check if ipykernel is installed in the environment."""
        try:
            result = self._run_in_dir(self._list_packages_cmd)
            return "ipykernel" in result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def get_relative_path(self) -> Path:
        """Get dir path relative to cwd"""
        try:
            return self.env_dir.relative_to(Path.cwd())
        except ValueError:
            return self.env_dir

    def get_activate_msg(self) -> str:
        """Get a message explaining how to activate"""
        return (
            f"Activate with: [green]source "
            f"{self.get_relative_path() / '.venv/bin/activate'}[/green]"
        )

    def get_relative_path_log_file(self) -> Path:
        """Get the relative path of the log file"""
        return self.get_relative_path() / self.path_log_file.name


class PixiEnvironment(Environment):
    """Pixi environment management.

    Args:
        env_dir: Directory containing pixi.toml and pixi.lock
        name: Optional name for the environment

    Raises:
        FileNotFoundError: If pixi is not installed
    """

    tool_name = "pixi"
    _tool_install_url = "https://pixi.sh"
    _install_cmd = "pixi install -v"
    _list_packages_cmd = "pixi list"

    def _detect_name(self) -> str:
        """Detect environment name from pixi.toml."""
        pixi_toml = self.env_dir / "pixi.toml"
        with open(pixi_toml, "rb") as file:
            config = tomllib.load(file)
        return config.get("project", {}).get("name", self.env_dir.name)

    def list_packages(self) -> list[str]:
        """List installed packages in the environment.

        Returns:
            List of package names
        """
        result = self._run_in_dir("pixi list")
        # Parse package names from output
        packages = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                # Extract package name (first column)
                parts = line.split()
                if parts:
                    packages.append(parts[0])
        return packages

    def get_activate_msg(self) -> str:
        return (
            f"Activate with: [green]pixi shell --manifest-path "
            f"{self.get_relative_path()}[/green]"
        )


class UvPylockEnvironment(Environment):
    """UV environment management using pylock.toml.

    Args:
        env_dir: Directory containing pylock.toml
        name: Optional name for the environment

    Raises:
        FileNotFoundError: If uv is not installed
    """

    tool_name = "uv"
    _tool_install_url = "https://github.com/astral-sh/uv"
    _venv_dir = ".venv"
    _list_packages_cmd = "uv pip list"

    def _detect_name(self) -> str:
        """Detect environment name from pylock.toml."""
        pylock_toml = self.env_dir / "pylock.toml"
        try:
            with open(pylock_toml, "rb") as file:
                config = tomllib.load(file)
            return config.get("project", {}).get("name", self.env_dir.name)
        except FileNotFoundError:
            return self.env_dir.name

    def install(self) -> None:
        """Install the uv environment from pylock.toml.

        Raises:
            subprocess.CalledProcessError: If installation fails
        """
        with open(self.path_log_file, "w", encoding="utf-8") as file:
            if not self.venv_path.exists():
                self._run_in_dir("uv venv", log_file=file)
            self._run_in_dir(["uv", "pip", "sync", "pylock.toml"], log_file=file)


class PyProjectEnvironment(Environment):
    def _detect_name(self) -> str:
        """Detect environment name from pyproject.toml."""
        pyproject_toml = self.env_dir / "pyproject.toml"
        try:
            with open(pyproject_toml, "rb") as file:
                config = tomllib.load(file)
            return config.get("project", {}).get("name", self.env_dir.name)
        except FileNotFoundError:
            return self.env_dir.name


class UvEnvironment(PyProjectEnvironment):
    """UV environment management using uv.lock.

    Args:
        env_dir: Directory containing uv.lock and pyproject.toml
        name: Optional name for the environment

    Raises:
        FileNotFoundError: If uv is not installed
    """

    tool_name = "uv"
    _tool_install_url = "https://github.com/astral-sh/uv"
    _venv_dir = ".venv"
    _install_cmd = "uv sync"
    _list_packages_cmd = "uv list"


class PdmEnvironment(PyProjectEnvironment):
    """PDM environment management using pdm.lock.

    Args:
        env_dir: Directory containing pdm.lock and pyproject.toml
        name: Optional name for the environment

    Raises:
        FileNotFoundError: If pdm is not installed
    """

    tool_name = "pdm"
    _tool_install_url = "https://pdm-project.org"
    _install_cmd = "pdm sync"
    _list_packages_cmd = "pdm list"


supported_tools = {
    "pixi": PixiEnvironment,
    "uv-pylock": UvPylockEnvironment,
    "uv": UvEnvironment,
    "pdm": PdmEnvironment,
    "pdm-uv": PdmEnvironment,
}


def create_env_object(env_type: str, env_dir: Path) -> Environment:
    """Install a pixi environment.

    Args:
        env_dir: Directory containing pixi.toml and pixi.lock

    Returns:
        Name of the installed environment
    """
    cls = supported_tools[env_type]
    return cls(env_dir)
