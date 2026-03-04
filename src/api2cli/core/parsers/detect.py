from __future__ import annotations

import json

import yaml

from api2cli.models.spec import SpecFormat


def detect_format(content: str) -> SpecFormat:
    """Detect the format of an API spec from its content.

    Args:
        content: Raw spec content string.

    Returns:
        The detected SpecFormat.
    """
    content_stripped = content.strip()

    # Try to parse as JSON or YAML to inspect structure
    try:
        if content_stripped.startswith("{"):
            data = json.loads(content_stripped)
        else:
            data = yaml.safe_load(content_stripped)
    except Exception:
        return SpecFormat.UNKNOWN

    if not isinstance(data, dict):
        return SpecFormat.UNKNOWN

    # OpenAPI detection
    if "openapi" in data or "swagger" in data:
        return SpecFormat.OPENAPI

    # HAR detection
    if "log" in data and isinstance(data.get("log"), dict):
        log = data["log"]
        if "entries" in log or "version" in log:
            return SpecFormat.HAR

    # GraphQL SDL detection (not JSON/YAML)
    return SpecFormat.UNKNOWN


def detect_format_from_string(content: str) -> SpecFormat:
    """Detect format, also checking for GraphQL SDL.

    Args:
        content: Raw spec content string.

    Returns:
        The detected SpecFormat.
    """
    stripped = content.strip()

    # GraphQL SDL heuristic: contains 'type Query' or 'type Mutation'
    if (
        "type Query" in stripped
        or "type Mutation" in stripped
        or stripped.startswith("schema {")
        or stripped.startswith("type ")
    ):
        return SpecFormat.GRAPHQL

    return detect_format(stripped)
