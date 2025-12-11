# How to contribute to install-locked-env

Thank you for considering contributing to install-locked-env.

## Reporting Issues

When opening an issue to report a problem
(<https://foss.heptapod.net/fluiddyn/install-locked-env/issues>), please try to provide a
minimal code example that reproduces the issue along with details of the system you are
using.

## Development process

For install-locked-env, we use the revision control software Mercurial and our main
repository is hosted here: <https://foss.heptapod.net/fluiddyn/install-locked-env>.

We use a standard modern Mercurial workflow based on Mercurial topics (which are nice
feature branches). Don't be afraid it's very simple. You should find all the needed
informations in these two pages:

- https://fluidhowto.readthedocs.io/en/latest/mercurial/install-setup.html
- https://fluidhowto.readthedocs.io/en/latest/mercurial/heptapod-workflow.html

## Developer setup

### Local developer installation

We use [PDM], which can for example be installed with [UV] with `uv tool install pdm`.

```sh
hg clone ssh://hg@foss.heptapod.net/fluiddyn/install-locked-env
cd install-locked-env
pdm sync
. .venv/bin/activate
```

### Running Tests

```sh
# Run all tests
pytest

# Run with coverage
pytest --cov=install_locked_env --cov-report=html

# Run specific test file
pytest tests/test_parsers.py

# Run specific test
pytest tests/test_parsers.py::test_parse_github_url
```

[pdm]: https://pdm-project.org
[uv]: https://docs.astral.sh/uv/
