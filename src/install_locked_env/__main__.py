"""CLI for install-locked-env."""

from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .parsers import parse_url
from .downloaders import download_files_choose_tool
from .environments import create_env_object, supported_tools

app = typer.Typer(
    help="Install locked environments from web sources",
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


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
    register_kernel: bool = typer.Option(
        True,
        "--register-kernel/--no-register-kernel",
        help="Register Jupyter kernel if ipykernel is present",
    ),
    version: Annotated[
        Optional[bool],
        typer.Option("--version", callback=version_callback, is_eager=True),
    ] = None,
) -> None:
    """Install a locked environment from a web source."""

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Parse URL
        task = progress.add_task("Parsing URL...", total=None)
        try:
            url_info = parse_url(url)
            console.print(f"[green]✓[/green] Detected {url_info.platform} repository")
            console.print(f"  Repository: {url_info.owner}/{url_info.repo}")
            if url_info.path:
                console.print(f"  Path: {url_info.path}")
        except ValueError as exc:
            console.print(f"[red]✗[/red] {exc}")
            raise typer.Exit(1)
        progress.remove_task(task)

        # Download files
        task = progress.add_task("Downloading files...", total=None)
        try:
            env_type, files = download_files_choose_tool(url_info)
            console.print(f"[green]✓[/green] Downloaded {len(files)} file(s)")
            console.print(f"  Environment type: {env_type}")
        except Exception as exc:
            console.print(f"[red]✗[/red] Failed to download: {exc}")
            raise typer.Exit(1)
        progress.remove_task(task)

        # Determine output directory
        if output_dir is None:
            env_name = url_info.path.rstrip("/").split("/")[-1]
            if not env_name:
                env_name = f"env-{url_info.repo}"
            output_dir = Path.cwd() / env_name

        output_dir.mkdir(parents=True, exist_ok=True)

        # Save files
        task = progress.add_task("Saving files...", total=None)
        for filename, content in files.items():
            (output_dir / filename).write_text(content)
        console.print(f"[green]✓[/green] Saved files to {output_dir}")
        console.print("    " + ", ".join(files.keys()))
        progress.remove_task(task)

        if no_install:
            console.print("[yellow]Skipping installation (--no-install)[/yellow]")
            return

        # Install environment
        if env_type in supported_tools:
            env = create_env_object(env_type, output_dir)
            task = progress.add_task(
                f"  Installing {env.tool_name} environment...", total=None
            )
            console.print(
                f"  log file installation: {env.get_relative_path_log_file()}"
            )
            try:
                env.install()
                console.print(f"[green]✓[/green] Installed environment: {env.name}")
            except Exception as exc:
                console.print(f"[red]✗[/red] Installation failed: {exc}")
                raise typer.Exit(1)
            progress.remove_task(task)

            # Register Jupyter kernel if requested
            if register_kernel:
                task = progress.add_task("Checking for ipykernel...", total=None)
                if env.register_jupyter_kernel():
                    console.print("[green]✓[/green] Registered Jupyter kernel")
                else:
                    console.print(
                        "[yellow]⚠[/yellow] ipykernel not found, skipping kernel registration"
                    )
                progress.remove_task(task)
        else:
            console.print(f"[red]✗[/red] Unsupported environment type: {env_type}")
            raise typer.Exit(1)

    console.print("[bold green]Installation complete![/bold green]")
    console.print(env.get_activate_msg())


def cli():
    """"""
    app()


if __name__ == "__main__":
    cli()
