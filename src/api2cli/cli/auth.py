from __future__ import annotations

from typing import Annotated

import typer

from api2cli.models.config import AuthConfig, Credential
from api2cli.plugins.auth.credential_store import CredentialStore

auth_app = typer.Typer(name="auth", help="Manage authentication credentials.")

_VALID_TYPES = ("bearer", "apikey", "basic")


@auth_app.command("set")
def set_cred(
    spec: Annotated[str, typer.Option("--spec", "-s", help="Spec identifier (path or name)")],
    type: Annotated[
        str, typer.Option("--type", "-t", help="Auth type: bearer, apikey, basic")
    ],
    value: Annotated[str, typer.Option("--value", "-v", help="Credential value")],
) -> None:
    """Store credentials for an API spec."""
    if type not in _VALID_TYPES:
        typer.echo(f"Error: --type must be one of: {', '.join(_VALID_TYPES)}", err=True)
        raise typer.Exit(code=1)

    if type == "bearer":
        auth_cfg = AuthConfig(type="bearer", token=value)
    elif type == "apikey":
        auth_cfg = AuthConfig(type="apikey", key_value=value)
    else:
        parts = value.split(":", 1)
        if len(parts) != 2:
            typer.echo("Error: basic auth value must be 'username:password'", err=True)
            raise typer.Exit(code=1)
        auth_cfg = AuthConfig(type="basic", username=parts[0], password=parts[1])

    store = CredentialStore()
    credential = Credential(api_id=spec, auth_config=auth_cfg)
    store.set(spec, credential)
    typer.echo(f"Credentials stored for '{spec}'.")


@auth_app.command("status")
def status(
    spec: Annotated[str, typer.Option("--spec", "-s", help="Spec identifier")],
) -> None:
    """Show stored credentials for an API spec."""
    store = CredentialStore()
    credential = store.get(spec)
    if credential is None:
        typer.echo(f"No credentials stored for '{spec}'.")
        raise typer.Exit(code=1)

    auth = credential.auth_config
    typer.echo(f"Spec:    {spec}")
    typer.echo(f"Type:    {auth.type}")
    if auth.type == "bearer":
        masked = (auth.token or "")[:4] + "****" if auth.token else "(none)"
        typer.echo(f"Token:   {masked}")
    elif auth.type == "apikey":
        masked = (auth.key_value or "")[:4] + "****" if auth.key_value else "(none)"
        typer.echo(f"Key:     {masked}")
    elif auth.type == "basic":
        typer.echo(f"User:    {auth.username or '(none)'}")
    typer.echo(f"Stored:  {credential.created_at.date()}")


@auth_app.command("clear")
def clear(
    spec: Annotated[str, typer.Option("--spec", "-s", help="Spec identifier")],
) -> None:
    """Remove stored credentials for an API spec."""
    store = CredentialStore()
    removed = store.delete(spec)
    if removed:
        typer.echo(f"Credentials cleared for '{spec}'.")
    else:
        typer.echo(f"No credentials found for '{spec}'.")
        raise typer.Exit(code=1)


@auth_app.command("list")
def list_all() -> None:
    """List all stored credential references."""
    store = CredentialStore()
    refs = store.list_refs()
    if not refs:
        typer.echo("No credentials stored.")
        return
    for ref in refs:
        typer.echo(ref)
