from install_locked_env.__main__ import cli


def __getattr__(name: str):
    if name == "__version__":
        from install_locked_env._version import __version__

        return __version__

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
