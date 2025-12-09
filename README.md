# install-locked-env

Helper to install (web) locked environments.

## Installation

### Development Setup

```bash
hg clone ssh://hg@foss.heptapod.net/fluiddyn/install-locked-env
cd install-locked-env
pdm sync
```

### Installing as a tool

Once published to PyPI, you can use it with `uvx`:

```bash
uvx install-locked-env <url>
```

## Usage

### Basic Usage

Install a locked environment from a web source:

```bash
install-locked-env https://github.com/fluiddyn/fluidsim/tree/5266c974e3368d17819f59b0e700b723591e0d1a/pixi-envs/env-fluidsim-mpi
```

### Options

```bash
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
```bash
install-locked-env https://github.com/fluiddyn/fluidsim/tree/main/pixi-envs/env-fluidsim
```

**Install from Heptapod:**
```bash
install-locked-env https://foss.heptapod.net/fluiddyn/fluidsim/-/tree/branch/default/pixi-envs/env-fluidsim
```

**Install from GitLab:**
```bash
install-locked-env https://gitlab.com/user/project/-/tree/main/envs/dev
```

**Download only (no installation):**
```bash
install-locked-env --no-install --output ./my-env https://github.com/user/repo/tree/main/envs/prod
```

**Skip Jupyter kernel registration:**
```bash
install-locked-env --no-register-kernel https://github.com/user/repo/tree/main/envs/test
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=install_locked_env --cov-report=html

# Run specific test file
pytest tests/test_parsers.py

# Run specific test
pytest tests/test_parsers.py::test_parse_github_url
```

## Supported Platforms

- ✅ GitHub
- ✅ GitLab
- ✅ Heptapod

## Supported Environment Types

### Current (v0.1.0)
- ✅ Pixi (pixi.toml, pixi.lock)

### Planned
- ⏳ uv (pyproject.toml, uv.lock)
- ⏳ PDM (pyproject.toml, pdm.lock)
- ⏳ Poetry (pyproject.toml, poetry.lock)

## How It Works

1. **URL Parsing**: Extracts repository information (platform, owner, repo, ref, path)
2. **File Detection**: Attempts to download supported lock files
3. **Environment Type Detection**: Determines the type based on downloaded files
4. **Installation**: Creates output directory and runs the appropriate installer
5. **Jupyter Registration**: If ipykernel is present, registers the environment as a Jupyter kernel

## Requirements

- Python 3.11+
- pixi (for pixi environments)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Your License Here]