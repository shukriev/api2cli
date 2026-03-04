from __future__ import annotations

from typing import Annotated

import typer

from api2cli.cli.command_router import CommandRouter, RoutingError
from api2cli.cli.introspection import capabilities_output, describe_output
from api2cli.cli.spec_loader import load_spec
from api2cli.core.analyzer.analyzer import DefaultAnalyzer
from api2cli.core.generator.generator import DefaultGenerator
from api2cli.core.runtime.request_builder import RequestBuilder, build_curl_command
from api2cli.core.runtime.response_transformer import ResponseTransformer
from api2cli.errors import AuthError, Ok
from api2cli.models.commands import OutputFormat


def _build_tree(spec_path: str):  # type: ignore[no-untyped-def]
    """Load spec, analyze, and generate command tree."""
    spec = load_spec(spec_path)
    analyzer = DefaultAnalyzer()
    analyze_result = analyzer.analyze(spec)
    if not isinstance(analyze_result, Ok):
        typer.echo(f"Error: {analyze_result.error.message}", err=True)
        raise typer.Exit(code=1)
    generator = DefaultGenerator()
    gen_result = generator.generate(analyze_result.value)
    if not isinstance(gen_result, Ok):
        typer.echo(f"Error: {gen_result.error.message}", err=True)
        raise typer.Exit(code=1)
    return gen_result.value


def run_command(
    ctx: typer.Context,
    spec: Annotated[str, typer.Option("--spec", "-s", help="Path to API spec file")] = "",
    capabilities: Annotated[
        bool, typer.Option("--capabilities", help="Print capabilities JSON and exit")
    ] = False,
    describe: Annotated[
        str | None, typer.Option("--describe", help="Describe a command (e.g. pets.list)")
    ] = None,
    output: Annotated[
        str,
        typer.Option("--output", "-o", help="Output format (json, table, csv, yaml, ndjson, ai)"),
    ] = "json",
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Print curl command without executing")
    ] = False,
    auth_token: Annotated[
        str | None,
        typer.Option("--auth-token", help="Bearer token for authentication"),
    ] = None,
    api_key: Annotated[
        str | None,
        typer.Option("--api-key", help="API key for authentication"),
    ] = None,
    basic_auth: Annotated[
        str | None,
        typer.Option("--basic-auth", help="Basic auth credentials (username:password)"),
    ] = None,
) -> None:
    """Run commands against an API spec dynamically."""
    if not spec and not capabilities and describe is None:
        typer.echo(ctx.get_help())
        return

    if not spec:
        typer.echo("Error: --spec is required", err=True)
        raise typer.Exit(code=1)

    tree = _build_tree(spec)

    if capabilities:
        typer.echo(capabilities_output(tree))
        raise typer.Exit(code=0)

    if describe is not None:
        result = describe_output(tree, describe)
        if result is None:
            typer.echo(f"Error: Command '{describe}' not found", err=True)
            raise typer.Exit(code=1)
        typer.echo(result)
        raise typer.Exit(code=0)

    remaining = ctx.args
    if not remaining:
        typer.echo(ctx.get_help())
        return

    router = CommandRouter()
    try:
        parsed = router.route(tree, remaining)
    except RoutingError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    node = parsed.node
    if not node.execution:
        typer.echo(f"Would execute: {' '.join(node.path)}")
        return

    base_url = tree.meta.base_urls[0] if tree.meta.base_urls else "https://localhost"
    builder = RequestBuilder()
    request = builder.build(node, parsed.flag_values, base_url)

    if node.execution.security_requirements:
        from api2cli.plugins.auth.resolver import AuthResolver

        cli_flags: dict[str, str] = {}
        if auth_token:
            cli_flags["auth_token"] = auth_token
        if api_key:
            cli_flags["api_key"] = api_key
        if basic_auth:
            cli_flags["basic_auth"] = basic_auth

        resolver = AuthResolver()
        try:
            apply_auth = resolver.resolve(
                security_schemes=tree.meta.security_schemes,
                security_requirements=node.execution.security_requirements,
                cli_flags=cli_flags,
            )
            request = apply_auth(request)
        except AuthError as exc:
            typer.echo(f"Error: {exc.message}", err=True)
            raise typer.Exit(code=1) from exc

    if dry_run:
        curl = build_curl_command(request)
        typer.echo(curl)
        return

    from api2cli.core.runtime.http_executor import HttpxExecutor
    from api2cli.plugins.output import format_output

    executor = HttpxExecutor()
    exec_result = executor.execute_sync(request)

    if not isinstance(exec_result, Ok):
        typer.echo(f"Error: {exec_result.error.message}", err=True)
        raise typer.Exit(code=1)

    transformer = ResponseTransformer()
    envelope = transformer.transform(exec_result.value, command=" ".join(node.path))

    try:
        fmt = OutputFormat(output.lower())
    except ValueError:
        fmt = OutputFormat.JSON

    typer.echo(format_output(envelope, fmt))

    if envelope.error:
        raise typer.Exit(code=1)
