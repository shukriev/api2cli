from __future__ import annotations

import json

from api2cli.models.runtime import OutputEnvelope


class JsonFormatter:
    """Formats OutputEnvelope as JSON."""

    def __init__(self, compact: bool = False, indent: int = 2) -> None:
        self._compact = compact
        self._indent = indent

    def format(self, envelope: OutputEnvelope) -> str:
        if envelope.error:
            output = {
                "error": {
                    "code": envelope.error.code,
                    "message": envelope.error.message,
                    "details": envelope.error.details,
                }
            }
        else:
            output = envelope.data

        if self._compact:
            return json.dumps(output, default=str, separators=(",", ":"))
        return json.dumps(output, indent=self._indent, default=str)
