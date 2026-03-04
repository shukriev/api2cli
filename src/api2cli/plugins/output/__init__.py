from __future__ import annotations

from api2cli.models.commands import OutputFormat
from api2cli.models.runtime import OutputEnvelope
from api2cli.plugins.output.json_formatter import JsonFormatter
from api2cli.plugins.output.table_formatter import TableFormatter


def format_output(envelope: OutputEnvelope, fmt: OutputFormat) -> str:
    """Format output using the specified formatter.

    Args:
        envelope: The output envelope to format.
        fmt: The desired output format.

    Returns:
        Formatted string output.
    """
    if fmt == OutputFormat.TABLE:
        return TableFormatter().format(envelope)
    compact = fmt == OutputFormat.NDJSON
    return JsonFormatter(compact=compact).format(envelope)


__all__ = ["JsonFormatter", "TableFormatter", "format_output"]
