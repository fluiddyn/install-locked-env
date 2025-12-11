"""Environment management classes."""

import subprocess
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

    def __init__(self, env_dir: Path, name: Optional[str] = None):
        self._check_tool()
        self.env_dir = Path(env_dir)
        self._name = name
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
        pass

    @abstractmethod
    def install(self) -> None:
        """Install the environment."""
        pass

    @abstractmethod
    def run_in_env(self, command: list[str], **kwargs) -> subprocess.CompletedProcess:
        """Run a command in the environment.

        Args:
            command: Command to run as a list of strings
            **kwargs: Additional arguments to pass to subprocess.run

        Returns:
            CompletedProcess object
        """
        pass

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

    @abstractmethod
    def _has_ipykernel(self) -> bool:
        """Check if ipykernel is installed in the environment."""
        pass


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

    def _detect_name(self) -> str:
        """Detect environment name from pixi.toml."""
        pixi_toml = self.env_dir / "pixi.toml"
        with open(pixi_toml, "rb") as file:
            config = tomllib.load(file)
        return config.get("project", {}).get("name", self.env_dir.name)

    def install(self) -> None:
        """Install the pixi environment.

        Raises:
            subprocess.CalledProcessError: If installation fails
        """
        subprocess.run(
            ["pixi", "install"],
            cwd=self.env_dir,
            capture_output=True,
            text=True,
            check=True,
        )

    def run_in_env(self, command: list[str], **kwargs) -> subprocess.CompletedProcess:
        """Run a command in the pixi environment.

        Args:
            command: Command to run as a list of strings
            **kwargs: Additional arguments to pass to subprocess.run

        Returns:
            CompletedProcess object
        """
        # Default kwargs
        default_kwargs = {
            "cwd": self.env_dir,
            "capture_output": True,
            "text": True,
        }
        default_kwargs.update(kwargs)

        return subprocess.run(
            ["pixi", "run"] + command,
            **default_kwargs,
        )

    def _has_ipykernel(self) -> bool:
        """Check if ipykernel is installed in the pixi environment."""
        try:
            result = self.run_in_env(["pixi", "list"], check=True)
            return "ipykernel" in result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def list_packages(self) -> list[str]:
        """List installed packages in the environment.

        Returns:
            List of package names
        """
        result = subprocess.run(
            ["pixi", "list"],
            cwd=self.env_dir,
            capture_output=True,
            text=True,
            check=True,
        )
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
        # Create venv if it doesn't exist
        if not self.venv_path.exists():
            subprocess.run(
                ["uv", "venv"],
                cwd=self.env_dir,
                capture_output=True,
                text=True,
                check=True,
            )

        # Sync dependencies from pylock.toml
        subprocess.run(
            ["uv", "pip", "sync", "pylock.toml"],
            cwd=self.env_dir,
            capture_output=True,
            text=True,
            check=True,
        )

    def run_in_env(self, command: list[str], **kwargs) -> subprocess.CompletedProcess:
        """Run a command in the uv environment.

        Args:
            command: Command to run as a list of strings
            **kwargs: Additional arguments to pass to subprocess.run

        Returns:
            CompletedProcess object
        """
        default_kwargs = {
            "cwd": self.env_dir,
            "capture_output": True,
            "text": True,
        }
        default_kwargs.update(kwargs)

        # Use uv run to execute in the environment
        return subprocess.run(
            ["uv", "run"] + command,
            **default_kwargs,
        )

    def _has_ipykernel(self) -> bool:
        """Check if ipykernel is installed in the uv environment."""
        try:
            result = self.run_in_env(["python", "-m", "pip", "list"], check=True)
            return "ipykernel" in result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


class UvEnvironment(Environment):
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

    def _detect_name(self) -> str:
        """Detect environment name from pyproject.toml."""
        pyproject_toml = self.env_dir / "pyproject.toml"
        try:
            with open(pyproject_toml, "rb") as file:
                config = tomllib.load(file)
            return config.get("project", {}).get("name", self.env_dir.name)
        except FileNotFoundError:
            return self.env_dir.name

    def install(self) -> None:
        """Install the uv environment from uv.lock.

        Raises:
            subprocess.CalledProcessError: If installation fails
        """
        # uv sync will create venv and install dependencies
        subprocess.run(
            ["uv", "sync"],
            cwd=self.env_dir,
            capture_output=True,
            text=True,
            check=True,
        )

    def run_in_env(self, command: list[str], **kwargs) -> subprocess.CompletedProcess:
        """Run a command in the uv environment.

        Args:
            command: Command to run as a list of strings
            **kwargs: Additional arguments to pass to subprocess.run

        Returns:
            CompletedProcess object
        """
        default_kwargs = {
            "cwd": self.env_dir,
            "capture_output": True,
            "text": True,
        }
        default_kwargs.update(kwargs)

        # Use uv run to execute in the environment
        return subprocess.run(
            ["uv", "run"] + command,
            **default_kwargs,
        )

    def _has_ipykernel(self) -> bool:
        """Check if ipykernel is installed in the uv environment."""
        try:
            result = self.run_in_env(["python", "-m", "pip", "list"], check=True)
            return "ipykernel" in result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


class PdmEnvironment(Environment):
    """PDM environment management using pdm.lock.

    Args:
        env_dir: Directory containing pdm.lock and pyproject.toml
        name: Optional name for the environment

    Raises:
        FileNotFoundError: If pdm is not installed
    """

    tool_name = "pdm"
    _tool_install_url = "https://pdm-project.org"

    def _detect_name(self) -> str:
        """Detect environment name from pyproject.toml."""
        pyproject_toml = self.env_dir / "pyproject.toml"
        try:
            with open(pyproject_toml, "rb") as file:
                config = tomllib.load(file)
            return config.get("project", {}).get("name", self.env_dir.name)
        except FileNotFoundError:
            return self.env_dir.name

    def install(self) -> None:
        """Install the pdm environment from pdm.lock.

        Raises:
            subprocess.CalledProcessError: If installation fails
        """
        subprocess.run(
            ["pdm", "install"],
            cwd=self.env_dir,
            capture_output=True,
            text=True,
            check=True,
        )

    def run_in_env(self, command: list[str], **kwargs) -> subprocess.CompletedProcess:
        """Run a command in the pdm environment.

        Args:
            command: Command to run as a list of strings
            **kwargs: Additional arguments to pass to subprocess.run

        Returns:
            CompletedProcess object
        """
        default_kwargs = {
            "cwd": self.env_dir,
            "capture_output": True,
            "text": True,
        }
        default_kwargs.update(kwargs)

        # Use pdm run to execute in the environment
        return subprocess.run(
            ["pdm", "run"] + command,
            **default_kwargs,
        )

    def _has_ipykernel(self) -> bool:
        """Check if ipykernel is installed in the pdm environment."""
        try:
            result = subprocess.run(
                ["pdm", "list"],
                cwd=self.env_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            return "ipykernel" in result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


supported_tools = {
    "pixi": PixiEnvironment,
    "uv-pylock": UvPylockEnvironment,
    "uv": UvEnvironment,
    "pdm": PdmEnvironment,
}


def create_env(env_type: str, env_dir: Path) -> Environment:
    """Install a pixi environment.

    Args:
        env_dir: Directory containing pixi.toml and pixi.lock

    Returns:
        Name of the installed environment
    """
    cls = supported_tools[env_type]
    env = cls(env_dir)
    env.install()
    return env
