from __future__ import annotations

from typing import Any

from api2cli.models.runtime import ApiResponse, OutputEnvelope, OutputError, OutputMeta


class ResponseTransformer:
    """Transforms ApiResponse objects into OutputEnvelope."""

    def transform(self, response: ApiResponse, command: str | None = None) -> OutputEnvelope:
        """Transform an API response into an OutputEnvelope.

        Args:
            response: The raw API response.
            command: The command that produced the response.

        Returns:
            OutputEnvelope with data, meta, and optional error.
        """
        meta = OutputMeta(
            command=command,
            url=None,
            method=None,
            timing=response.timing,
        )

        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        if any(k.startswith("x-ratelimit") or k == "ratelimit-limit" for k in headers_lower):
            from api2cli.models.runtime import RateLimitInfo

            meta.rate_limit = RateLimitInfo(
                limit=_parse_int(
                    headers_lower.get("x-ratelimit-limit")
                    or headers_lower.get("ratelimit-limit")
                ),
                remaining=_parse_int(
                    headers_lower.get("x-ratelimit-remaining")
                    or headers_lower.get("ratelimit-remaining")
                ),
            )

        if response.status_code >= 400:
            error_data: Any = response.body if isinstance(response.body, dict) else {}
            error_msg = (
                error_data.get("message")
                or error_data.get("error")
                or error_data.get("detail")
                or f"HTTP {response.status_code}"
            )
            return OutputEnvelope(
                data=None,
                meta=meta,
                error=OutputError(
                    code=f"HTTP_{response.status_code}",
                    message=str(error_msg),
                    http_status=response.status_code,
                    details=error_data if isinstance(error_data, dict) else {},
                ),
            )

        return OutputEnvelope(data=response.body, meta=meta)


def _parse_int(value: str | None) -> int | None:
    """Parse an integer from a string, returning None on failure.

    Args:
        value: String to parse.

    Returns:
        Parsed integer, or None if parsing fails.
    """
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None
