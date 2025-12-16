"""CLI for install-locked-env."""

from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .parsers import parse_url
from .downloaders import (
    download_files_choose_tool,
    download_repo_files,
    detect_env_type_from_dir,
)
from .environments import create_env_object, supported_tools

app = typer.Typer(
    help="Install locked environments from web sources",
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()
console_err = Console(stderr=True)


def version_callback(value: bool):
    if value:
        from install_locked_env._version import __version__

        print(__version__)
        raise typer.Exit()


@app.command()
def main(
    url: str = typer.Argument(..., help="URL to the locked environment source"),
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory (default: auto-generated)"
    ),
    no_install: bool = typer.Option(
        False, "--no-install", help="Download files only, don't install"
    ),
    no_register_kernel: bool = typer.Option(
        False,
        "--no-register-kernel",
        help="Don't register Jupyter kernel if ipykernel is present",
    ),
    version: Annotated[
        Optional[bool],
        typer.Option("--version", callback=version_callback, is_eager=True),
    ] = None,
    minimal: bool = typer.Option(
        False,
        "--minimal",
        help="Only download the files necessary to create the environment",
    ),
    clone: bool = typer.Option(
        False,
        "--clone",
        help="Clone the repo (only for repository url)",
    ),
    download_method: Optional[str] = typer.Option(
        None,
        "--download-method",
        "-d",
        help="Download method (default: auto): can be 'archive', 'file-per-file' or 'clone'",
    ),
) -> None:
    """Install a locked environment from a web source."""

    # unused argument
    del version

    if clone:
        if download_method is not None and download_method not in ("auto", "clone"):
            print("download method is incompatible with --clone")
            typer.Exit(1)
        download_method = "clone"

    if minimal:
        if download_method is not None and download_method != "auto":
            print("--minimal and --download-method are incompatible")
            typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Parse URL
        task = progress.add_task("Parsing URL...", total=None)
        try:
            url_info = parse_url(url)
        except ValueError as exc:
            console_err.print(f"[red]✗[/red] {exc}")
            raise typer.Exit(1)

        console.print(f"[green]✓[/green] Detected {url_info.platform} repository")
        console.print(f"  Repository: {url_info.owner}/{url_info.repo}")
        if url_info.path:
            console.print(f"  Path: {url_info.path}")
            if download_method == "clone":
                console_err.print("download method is incompatible with --clone")
                typer.Exit(1)

        progress.remove_task(task)

        # Determine output directory
        if output_dir is None:
            env_name = url_info.path.rstrip("/").split("/")[-1]
            if not env_name:
                env_name = f"env-{url_info.repo}"
            output_dir = Path.cwd() / env_name

        # Download files
        task = progress.add_task("Downloading files...", total=None)
        if minimal:
            try:
                env_type, files = download_files_choose_tool(url_info)
                console.print(f"[green]✓[/green] Downloaded {len(files)} file(s)")
            except Exception as exc:
                progress.remove_task(task)
                console_err.print(f"[red]✗[/red] Failed to download: {exc}")
                raise typer.Exit(1)
            progress.remove_task(task)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save files
            task = progress.add_task("Saving files...", total=None)
            for filename, content in files.items():
                (output_dir / filename).write_text(content)
        else:
            files = None
            try:
                download_repo_files(url_info, output_dir, download_method)
            except FileExistsError as exc:
                console_err.print(exc)
                progress.remove_task(task)
                raise typer.Exit(1)

            env_type = detect_env_type_from_dir(output_dir)

        console.print(f"[green]✓[/green] Saved files to {output_dir}")
        if files:
            console.print("    " + ", ".join(files.keys()))

        progress.remove_task(task)

        console.print(f"  Environment type: {env_type}")

        if no_install:
            console.print("[yellow]Skipping installation (--no-install)[/yellow]")
            return

        if env_type not in supported_tools:
            console_err.print(f"[red]✗[/red] Unsupported environment type: {env_type}")
            raise typer.Exit(1)

        # Install environment
        env = create_env_object(env_type, output_dir)
        task = progress.add_task(
            f"  Installing {env.tool_name} environment...", total=None
        )
        console.print(f"  log file installation: {env.get_relative_path_log_file()}")
        try:
            env.install()
            console.print(f"[green]✓[/green] Installed environment: {env.name}")
        except Exception as exc:
            console_err.print(f"[red]✗[/red] Installation failed: {exc}")
            raise typer.Exit(1)
        progress.remove_task(task)

        # Register Jupyter kernel if requested
        if not no_register_kernel:
            task = progress.add_task("Checking for ipykernel...", total=None)
            if env.register_jupyter_kernel():
                console.print("[green]✓[/green] Registered Jupyter kernel")
            else:
                console.print(
                    "[yellow]⚠[/yellow] ipykernel not found, skipping kernel registration"
                )
            progress.remove_task(task)

    console.print("[bold green]Installation complete![/bold green]")
    console.print(env.get_activate_msg())


if __name__ == "__main__":
    app()
