"""Environment installation utilities."""

from pathlib import Path

from install_locked_env.environments import PixiEnvironment


# Convenience functions to maintain backward compatibility
def install_pixi_env(env_dir: Path) -> str:
    """Install a pixi environment.

    Args:
        env_dir: Directory containing pixi.toml and pixi.lock

    Returns:
        Name of the installed environment
    """
    env = PixiEnvironment(env_dir)
    env.install()
    return env.name


def register_jupyter_kernel(env_dir: Path, env_name: str) -> bool:
    """Register the environment as a Jupyter kernel.

    Args:
        env_dir: Directory containing the pixi environment
        env_name: Name of the environment

    Returns:
        True if kernel was registered, False if ipykernel not found
    """
    env = PixiEnvironment(env_dir, name=env_name)
    return env.register_jupyter_kernel()
