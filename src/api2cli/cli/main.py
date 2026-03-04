from __future__ import annotations

import typer

from api2cli import __version__
from api2cli.cli.auth import auth_app
from api2cli.cli.run import run_command

app = typer.Typer(
    name="api2cli",
    help="Convert API specifications into AI-optimized CLI tools.",
    no_args_is_help=True,
)

app.command(
    "run",
    help="Run commands against an API spec.",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)(run_command)

app.add_typer(auth_app, name="auth")


@app.command()
def version() -> None:
    """Print the current version of api2cli."""
    typer.echo(f"api2cli {__version__}")


if __name__ == "__main__":
    app()
