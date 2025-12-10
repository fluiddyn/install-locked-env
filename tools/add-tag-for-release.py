#!/usr/bin/env -S uv run --script --no-project

import shlex
import subprocess
import sys

from pathlib import Path


def run(command, capture_output=False):
    process = subprocess.run(
        shlex.split(command),
        check=True,
        text=True,
        capture_output=capture_output,
        encoding="utf-8",
    )
    return process.stdout


def get_version_from_pyproject(path=Path.cwd()):
    if isinstance(path, str):
        path = Path(path)

    if path.name != "pyproject.toml":
        path /= "pyproject.toml"

    in_project = False
    version = None
    with open(path, encoding="utf-8") as file:
        for line in file:
            if line.startswith("[project]"):
                in_project = True
            if line.startswith("version =") and in_project:
                version = line.split("=")[1].strip()
                version = version[1:-1]
                break

    assert version is not None
    return version


def add_tag_for_release():
    """Add a tag to the repo for a new version"""
    run("hg pull")

    result = run("hg log -r default -G", capture_output=True)
    if result[0] != "@":
        run("hg update default")

    version = get_version_from_pyproject()

    print(f"{version = }")

    result = run("hg tags -T '{tag},'", capture_output=True)
    last_tag = result.split(",", 2)[1]
    print(f"{last_tag = }")

    if last_tag == version:
        print("last_tag == version", file=sys.stderr)
        sys.exit(1)

    answer = input(
        f'Do you really want to add and push the new tag "{version}"? (yes/[no]) '
    )

    if answer != "yes":
        print("Maybe next time then. Bye!")
        return

    print("Let's go!")
    run(f"hg tag {version}")
    run("hg push")


if __name__ == "__main__":
    add_tag_for_release()
