from __future__ import annotations

from pathlib import Path

import typer

from api2cli.core.parsers import parse_spec
from api2cli.core.parsers.spec_input import SpecInput
from api2cli.errors import Ok, ParseError
from api2cli.models.spec import ApiSpec


def _is_url(spec: str) -> bool:
    return spec.startswith("http://") or spec.startswith("https://")


def load_spec(spec: str) -> ApiSpec:
    """Load and parse an API spec from a file path or HTTP/HTTPS URL.

    Args:
        spec: File path or URL to the spec.

    Returns:
        Parsed ApiSpec.

    Raises:
        SystemExit: If the spec cannot be loaded or parsed.
    """
    try:
        if _is_url(spec):
            spec_input = SpecInput.from_url(spec)
        else:
            path = Path(spec)
            if not path.exists():
                typer.echo(f"Error: Spec file not found: {spec}", err=True)
                raise typer.Exit(code=1)
            spec_input = SpecInput.from_file(path)
    except ParseError as exc:
        typer.echo(f"Error: {exc.message}", err=True)
        raise typer.Exit(code=1) from exc

    result = parse_spec(spec_input)
    if not isinstance(result, Ok):
        typer.echo(f"Error: {result.error.message}", err=True)
        raise typer.Exit(code=1)

    return result.value
