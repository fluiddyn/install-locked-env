# install-locked-env

[![Latest version](https://img.shields.io/pypi/v/install-locked-env.svg)](https://pypi.python.org/pypi/install-locked-env/)
![Supported Python versions](https://img.shields.io/pypi/pyversions/install-locked-env.svg)
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![Heptapod CI](https://foss.heptapod.net/fluiddyn/install-locked-env/badges/branch/default/pipeline.svg)](https://foss.heptapod.net/fluiddyn/install-locked-env/-/pipelines)

A minimalist CLI tool easing the installation of "locked environments" stored in
repositories on the web.

## Installation

`install-locked-env` is a CLI tool available on PyPI so the simplest way to install and
run it is by using [UV] and more precisely its command `uvx`:

```sh
uvx install-locked-env <url>
```

## Usage

### Basic Usage

Install a locked environment from a web source:

```sh
install-locked-env https://github.com/fluiddyn/fluidsim/tree/branch/default/pixi-envs/env-fluidsim
```

Different lock file formats (pylock.toml, uv.lock, pdm.lock, pixi.lock, ...) produced and
used by different tools (UV, PDM, Pixi, ...) will be supported. Currently, only Pixi is
supported.

GitHub, GitLab and Heptapod are supported.

> ⚠️ **Caution**
>
> Use only with trusted repositories and lock files! `install-locked-env` potentially
> executes code in the installed environment.

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
# warning: currently uses pixi.lock instead of pylock.toml
install-locked-env https://github.com/fluiddyn/fluidsim
```

or in another directory:

```sh
install-locked-env https://github.com/fluiddyn/fluidsim/tree/branch/default/pixi-envs/env-fluidsim
```

or, with a precise commit reference:

```sh
install-locked-env https://github.com/fluiddyn/fluidsim/tree/5266c974e3368d17819f59b0e700b723591e0d1a/pixi-envs/env-fluidsim-mpi
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
install-locked-env --no-install --output ./my-env https://github.com/user/repo
```

**Skip Jupyter kernel registration:**

```sh
install-locked-env --no-register-kernel https://github.com/user/repo
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

Contributions are welcome! See [our contributing guide](./CONTRIBUTING.md).

## License

BSD-3-Clause

[uv]: https://docs.astral.sh/uv/
