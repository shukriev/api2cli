from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import httpx

from api2cli.errors import ParseError


@dataclass(frozen=True)
class SpecInput:
    """Input specification source — either file path or raw content string."""

    content: str
    source: str = "<string>"

    @classmethod
    def from_file(cls, path: Path) -> SpecInput:
        """Load spec content from a file path.

        Args:
            path: Path to the spec file.

        Returns:
            A SpecInput with the file's content.
        """
        content = path.read_text(encoding="utf-8")
        return cls(content=content, source=str(path))

    @classmethod
    def from_url(cls, url: str, timeout: float = 30.0) -> SpecInput:
        """Fetch spec content from an HTTP/HTTPS URL.

        Args:
            url: The URL to fetch the spec from.
            timeout: Request timeout in seconds.

        Returns:
            A SpecInput with the fetched content.

        Raises:
            ParseError: If the request fails or returns a non-2xx status.
        """
        try:
            response = httpx.get(url, timeout=timeout, follow_redirects=True)
        except httpx.TimeoutException as exc:
            raise ParseError(f"Timed out fetching spec from {url}") from exc
        except httpx.RequestError as exc:
            raise ParseError(f"Failed to fetch spec from {url}: {exc}") from exc

        if not response.is_success:
            raise ParseError(
                f"Fetching spec from {url} returned HTTP {response.status_code}"
            )

        return cls(content=response.text, source=url)

    @classmethod
    def from_string(cls, content: str, source: str = "<string>") -> SpecInput:
        """Create spec input from a raw string.

        Args:
            content: Raw spec content string.
            source: Optional source identifier for error messages.

        Returns:
            A SpecInput wrapping the given content.
        """
        return cls(content=content, source=source)
