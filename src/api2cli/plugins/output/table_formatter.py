from __future__ import annotations

import io
from typing import Any

from rich.console import Console
from rich.table import Table

from api2cli.models.runtime import OutputEnvelope


class TableFormatter:
    """Formats OutputEnvelope as a rich table."""

    def format(self, envelope: OutputEnvelope) -> str:
        if envelope.error:
            return f"Error: {envelope.error.code} - {envelope.error.message}"

        data = envelope.data
        if data is None:
            return "(no data)"

        if isinstance(data, list):
            return self._format_list(data)
        if isinstance(data, dict):
            return self._format_dict(data)
        return str(data)

    def _format_list(self, data: list[Any]) -> str:
        if not data:
            return "(empty list)"

        first = data[0]
        if not isinstance(first, dict):
            return "\n".join(str(item) for item in data)

        columns = list(first.keys())
        table = Table()
        for col in columns:
            table.add_column(str(col))

        for item in data:
            if isinstance(item, dict):
                table.add_row(*[str(item.get(col, "")) for col in columns])

        return self._render_table(table)

    def _format_dict(self, data: dict[str, Any]) -> str:
        table = Table()
        table.add_column("Key")
        table.add_column("Value")
        for key, value in data.items():
            table.add_row(str(key), str(value))
        return self._render_table(table)

    def _render_table(self, table: Table) -> str:
        console = Console(file=io.StringIO(), force_terminal=False)
        console.print(table)
        return console.file.getvalue()  # type: ignore[attr-defined]
