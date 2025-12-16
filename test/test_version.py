import install_locked_env


def test_version():
    """Test __version__"""
    assert isinstance(install_locked_env.__version__, str)
