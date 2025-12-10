# install-locked-env

Helper to install "locked environments" stored in repositories on the web.

## Installation

### Development Setup

```sh
hg clone ssh://hg@foss.heptapod.net/fluiddyn/install-locked-env
cd install-locked-env
pdm sync
. .venv/bin/activate
```

### Installing as a tool

Once published to PyPI, you can use it with `uvx`:

```sh
uvx install-locked-env <url>
```

## Usage

### Basic Usage

Install a locked environment from a web source:

```sh
install-locked-env https://github.com/fluiddyn/fluidsim/tree/5266c974e3368d17819f59b0e700b723591e0d1a/pixi-envs/env-fluidsim-mpi
```

Different lock file formats (pylock.toml, uv.lock, pdm.lock, pixi.lock, ...) produced and
used by different tools (UV, PDM, Pixi, ...) will be supported. Currently, only Pixi is
supported.

GitHub, GitLab and Heptapod are supported.

> \[!CAUTION\] Use only with trusted repositories and lock files! `install-locked-env`
> potentially executes code in the installed environment.

### Options

```sh
install-locked-env [OPTIONS] URL

Options:
  -o, --output PATH          Output directory (default: auto-generated from URL)
  --no-install               Download files only, don't install environment
  --register-kernel          Register Jupyter kernel if ipykernel is present (default: True)
  --no-register-kernel       Skip Jupyter kernel registration
  --help                     Show this message and exit
```

### Examples

**Install from GitHub:**

Lockfile located in the root directory of a repository:

```sh
# not yet implemented
install-locked-env https://github.com/fluiddyn/fluidsim
# implemented, but
#   - uses pixi.lock and not pylock.toml and
#   - wrong env name
install-locked-env https://github.com/fluiddyn/fluidsim/tree/branch/default
```

or in another directory (this is what currently works):

```sh
install-locked-env https://github.com/fluiddyn/fluidsim/tree/branch/default/pixi-envs/env-fluidsim
```

It should be possible (not yet implemented) to give a lock file address (something like
<https://github.com/fluiddyn/fluidsim/tree/branch/default/pylock.toml>).

**Install from Heptapod:**

```sh
install-locked-env https://foss.heptapod.net/fluiddyn/fluidsim/-/tree/branch/default/pixi-envs/env-fluidsim
```

**Install from GitLab:**

```sh
install-locked-env https://gitlab.com/user/project/-/tree/main/envs/dev
```

**Download only (no installation):**

```sh
install-locked-env --no-install --output ./my-env https://github.com/user/repo/tree/main/envs/prod
```

**Skip Jupyter kernel registration:**

```sh
install-locked-env --no-register-kernel https://github.com/user/repo/tree/main/envs/test
```

## Running Tests

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

## Supported Environment Types

### Current (v0.1.0)

- ✅ Pixi (pixi.toml, pixi.lock)

### Planned

- ⏳ uv (pyproject.toml, uv.lock/pylock.toml)
- ⏳ PDM (pyproject.toml, pdm.lock/pylock.toml)
- ⏳ Poetry (pyproject.toml, poetry.lock)

## How it works

1. **URL parsing**: Extracts repository information (platform, owner, repo, ref, path)
2. **File detection**: Attempts to download supported lock files
3. **Environment type detection**: Determines the type based on downloaded files
4. **Installation**: Creates output directory and runs the appropriate installer
5. **Jupyter registration**: If ipykernel is present, registers the environment as a
   Jupyter kernel

## Requirements

- Python 3.11+
- Pixi (for Pixi environments)
- UV (for uv.lock and pylock.toml)
- PDM (for pdm.lock)

## Contributing

Contributions are welcome! Please feel free to submit a Merge Request.

## License

BSD-3-Clause
