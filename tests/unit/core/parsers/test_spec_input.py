from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx

from api2cli.core.parsers.spec_input import SpecInput
from api2cli.errors import ParseError

_MINIMAL_SPEC = '{"openapi":"3.0.0","info":{"title":"T","version":"1"},"paths":{}}'


class TestSpecInputFromFile:
    def test_loads_content(self, tmp_path: Path) -> None:
        f = tmp_path / "spec.json"
        f.write_text(_MINIMAL_SPEC)
        si = SpecInput.from_file(f)
        assert si.content == _MINIMAL_SPEC
        assert si.source == str(f)


class TestSpecInputFromUrl:
    @respx.mock
    def test_fetches_content(self) -> None:
        respx.get("https://example.com/spec.yaml").mock(
            return_value=httpx.Response(200, text=_MINIMAL_SPEC)
        )
        si = SpecInput.from_url("https://example.com/spec.yaml")
        assert si.content == _MINIMAL_SPEC
        assert si.source == "https://example.com/spec.yaml"

    @respx.mock
    def test_follows_redirect(self) -> None:
        respx.get("https://example.com/spec").mock(
            return_value=httpx.Response(200, text=_MINIMAL_SPEC)
        )
        si = SpecInput.from_url("https://example.com/spec")
        assert si.content == _MINIMAL_SPEC

    @respx.mock
    def test_raises_on_404(self) -> None:
        respx.get("https://example.com/missing.yaml").mock(
            return_value=httpx.Response(404)
        )
        with pytest.raises(ParseError, match="HTTP 404"):
            SpecInput.from_url("https://example.com/missing.yaml")

    @respx.mock
    def test_raises_on_500(self) -> None:
        respx.get("https://example.com/error.yaml").mock(
            return_value=httpx.Response(500)
        )
        with pytest.raises(ParseError, match="HTTP 500"):
            SpecInput.from_url("https://example.com/error.yaml")

    @respx.mock
    def test_raises_on_network_error(self) -> None:
        respx.get("https://example.com/spec.yaml").mock(
            side_effect=httpx.ConnectError("connection refused")
        )
        with pytest.raises(ParseError, match="Failed to fetch"):
            SpecInput.from_url("https://example.com/spec.yaml")

    @respx.mock
    def test_raises_on_timeout(self) -> None:
        respx.get("https://example.com/spec.yaml").mock(
            side_effect=httpx.TimeoutException("timed out")
        )
        with pytest.raises(ParseError, match="Timed out"):
            SpecInput.from_url("https://example.com/spec.yaml")
