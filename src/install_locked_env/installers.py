"""Environment installation utilities."""

import subprocess
import shutil
from pathlib import Path
import tomllib


def install_pixi_env(env_dir: Path) -> str:
    """Install a pixi environment.

    Args:
        env_dir: Directory containing pixi.toml and pixi.lock

    Returns:
        Name of the installed environment

    Raises:
        FileNotFoundError: If pixi is not installed
        subprocess.CalledProcessError: If installation fails
    """
    # Check if pixi is available
    if not shutil.which("pixi"):
        raise FileNotFoundError(
            "pixi is not installed. Install it from https://pixi.sh"
        )

    # Read environment name from pixi.toml
    pixi_toml = env_dir / "pixi.toml"
    with open(pixi_toml, "rb") as file:
        config = tomllib.load(file)

    env_name = config.get("project", {}).get("name", env_dir.name)

    # Run pixi install
    subprocess.run(
        ["pixi", "install"],
        cwd=env_dir,
        capture_output=True,
        text=True,
        check=True,
    )

    return env_name


def register_jupyter_kernel(env_dir: Path, env_name: str) -> bool:
    """Register the environment as a Jupyter kernel if ipykernel is present.

    Args:
        env_dir: Directory containing the pixi environment
        env_name: Name of the environment

    Returns:
        True if kernel was registered, False if ipykernel not found
    """
    # Check if ipykernel is in the environment
    # Run pixi list to see installed packages
    try:
        result = subprocess.run(
            ["pixi", "list"],
            cwd=env_dir,
            capture_output=True,
            text=True,
            check=True,
        )

        if "ipykernel" not in result.stdout:
            return False

        # Register the kernel using pixi run
        subprocess.run(
            [
                "pixi",
                "run",
                "python",
                "-m",
                "ipykernel",
                "install",
                "--user",
                "--name",
                env_name,
                "--display-name",
                f"Python ({env_name})",
            ],
            cwd=env_dir,
            capture_output=True,
            text=True,
            check=True,
        )

        return True

    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
