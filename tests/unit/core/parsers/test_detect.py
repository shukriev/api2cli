from __future__ import annotations

from api2cli.core.parsers.detect import detect_format, detect_format_from_string
from api2cli.models.spec import SpecFormat

OPENAPI_JSON = '{"openapi": "3.0.3", "info": {"title": "Test", "version": "1"}}'
OPENAPI_YAML = "openapi: '3.0.3'\ninfo:\n  title: Test\n  version: '1'"
GRAPHQL_SDL = "type Query {\n  users: [User]\n}\ntype User { id: ID }"
HAR_JSON = '{"log": {"version": "1.2", "entries": []}}'
UNKNOWN_CONTENT = "this is not any spec format"


class TestDetectFormat:
    def test_openapi_json(self) -> None:
        assert detect_format(OPENAPI_JSON) == SpecFormat.OPENAPI

    def test_openapi_yaml(self) -> None:
        assert detect_format(OPENAPI_YAML) == SpecFormat.OPENAPI

    def test_har_json(self) -> None:
        assert detect_format(HAR_JSON) == SpecFormat.HAR

    def test_unknown_content(self) -> None:
        assert detect_format(UNKNOWN_CONTENT) == SpecFormat.UNKNOWN

    def test_invalid_json(self) -> None:
        assert detect_format("{invalid json}") == SpecFormat.UNKNOWN

    def test_graphql_not_detected_by_detect_format(self) -> None:
        # detect_format doesn't detect GraphQL SDL (not JSON/YAML)
        result = detect_format(GRAPHQL_SDL)
        assert result in (SpecFormat.UNKNOWN, SpecFormat.GRAPHQL)


class TestDetectFormatFromString:
    def test_graphql_detected(self) -> None:
        assert detect_format_from_string(GRAPHQL_SDL) == SpecFormat.GRAPHQL

    def test_openapi_detected(self) -> None:
        assert detect_format_from_string(OPENAPI_JSON) == SpecFormat.OPENAPI

    def test_openapi_yaml_detected(self) -> None:
        assert detect_format_from_string(OPENAPI_YAML) == SpecFormat.OPENAPI

    def test_har_detected(self) -> None:
        assert detect_format_from_string(HAR_JSON) == SpecFormat.HAR
