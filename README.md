# install-locked-env

[![Latest version](https://img.shields.io/pypi/v/install-locked-env.svg)](https://pypi.python.org/pypi/install-locked-env/)
![Supported Python versions](https://img.shields.io/pypi/pyversions/install-locked-env.svg)
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![Heptapod CI](https://foss.heptapod.net/fluiddyn/install-locked-env/badges/branch/default/pipeline.svg)](https://foss.heptapod.net/fluiddyn/install-locked-env/-/pipelines)

A minimalist CLI tool easing the local installation of "locked environments" described in
lock files available in repositories on the web.

## Installation

The simplest way to install and run `install-locked-env` is by using the [UV] command
`uvx`:

```sh
uvx install-locked-env <url>
```

Of course, `install-locked-env` can also be installed with `uv tool`, `pipx` or even
`pip`.

## Usage

### Basic Usage

Install a locked environment from a web source:

```sh
install-locked-env https://github.com/fluiddyn/fluidsim/tree/branch/default/pixi-envs/env-fluidsim
```

Different lock file formats (pylock.toml, uv.lock, pdm.lock, pixi.lock, ...) produced by
different tools (UV, PDM, Pixi, ...) are supported.

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

**Install from a repository URL:**

Lockfile located in the root directory of a repository:

```sh
install-locked-env https://foss.heptapod.net/py-edu-fr/py-edu-fr
```

GitHub, GitLab and Heptapod are supported.

**Install from a reference/directory URL:**

```sh
install-locked-env https://github.com/fluiddyn/fluidsim/tree/branch/default/pixi-envs/env-fluidsim
```

or, with a precise commit reference:

```sh
install-locked-env https://github.com/fluiddyn/fluidsim/tree/5266c974e3368d17819f59b0e700b723591e0d1a/pixi-envs/env-fluidsim-mpi
```

For GitLab and Heptapod, the URLs have this format:

```sh
install-locked-env https://gitlab.com/user/project/-/tree/branch-name/envs/dev
```

For example:

```sh
install-locked-env https://foss.heptapod.net/fluiddyn/fluidsim/-/tree/branch/default/pixi-envs/env-fluidsim
```

It should be possible (not yet implemented) to give a lock file address (something like
<https://github.com/fluiddyn/fluidsim/tree/branch/default/pylock.toml>).

**Download only (no installation):**

```sh
install-locked-env --no-install --output ./my-env https://github.com/user/repo
```

**Skip Jupyter kernel registration:**

```sh
install-locked-env --no-register-kernel https://github.com/user/repo
```

## Supported Environment Types

### Current (v0.2.0)

- ✅ Pixi (pixi.toml, pixi.lock)
- ✅ uv (pyproject.toml, uv.lock/pylock.toml)
- ✅ PDM (pyproject.toml, pdm.lock/pylock.toml)

### Planned

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
