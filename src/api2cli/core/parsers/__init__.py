from __future__ import annotations

from api2cli.core.parsers.detect import detect_format, detect_format_from_string
from api2cli.core.parsers.openapi_parser import OpenApiParser
from api2cli.core.parsers.spec_input import SpecInput
from api2cli.errors import Err, Ok, ParseError
from api2cli.models.spec import ApiSpec, SpecFormat

type Result[T] = Ok[T] | Err[T]


def get_parser(fmt: SpecFormat) -> OpenApiParser:
    """Get a parser for the given spec format.

    Args:
        fmt: The spec format to get a parser for.

    Returns:
        An appropriate parser instance.

    Raises:
        ParseError: If no parser is available for the format.
    """
    if fmt == SpecFormat.OPENAPI:
        return OpenApiParser()
    raise ParseError(f"No parser available for format: {fmt}")


def parse_spec(spec_input: SpecInput) -> Ok[ApiSpec] | Err[ParseError]:
    """Parse a spec from a SpecInput.

    Detects format automatically and delegates to the appropriate parser.

    Args:
        spec_input: The spec input to parse.

    Returns:
        Ok(ApiSpec) on success, Err(ParseError) on failure.
    """
    fmt = detect_format_from_string(spec_input.content)

    if fmt == SpecFormat.UNKNOWN:
        return Err(ParseError(f"Could not detect spec format for {spec_input.source}"))

    try:
        parser = get_parser(fmt)
    except ParseError as exc:
        return Err(exc)

    return parser.parse(spec_input.content, source=spec_input.source)  # type: ignore[return-value]


__all__ = [
    "OpenApiParser",
    "SpecInput",
    "detect_format",
    "detect_format_from_string",
    "get_parser",
    "parse_spec",
]
