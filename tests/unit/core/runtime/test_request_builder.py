from __future__ import annotations

import pytest

from api2cli.core.runtime.request_builder import RequestBuilder, build_curl_command
from api2cli.models.commands import CommandNode, ExecutionDef, FlagDef, FlagType
from api2cli.models.runtime import ApiRequest


def make_command_node(
    method: str = "GET",
    url_template: str = "/items",
    path_params: list[str] | None = None,
    query_params: list[str] | None = None,
    header_params: list[str] | None = None,
    body_param: str | None = None,
    flags: list[FlagDef] | None = None,
) -> CommandNode:
    """Create a test CommandNode with the given parameters."""
    return CommandNode(
        name="test",
        path=["test"],
        execution=ExecutionDef(
            method=method,
            url_template=url_template,
            path_params=path_params or [],
            query_params=query_params or [],
            header_params=header_params or [],
            body_param=body_param,
        ),
        flags=flags or [],
    )


class TestRequestBuilder:
    def setup_method(self) -> None:
        self.builder = RequestBuilder()
        self.base_url = "https://api.example.com"

    def test_simple_get_request(self) -> None:
        node = make_command_node("GET", "/items")
        request = self.builder.build(node, {}, self.base_url)
        assert request.method == "GET"
        assert request.url == "https://api.example.com/items"

    def test_path_param_substitution(self) -> None:
        node = make_command_node(
            "GET",
            "/items/{itemId}",
            path_params=["itemId"],
            flags=[FlagDef(name="item-id", type=FlagType.STRING, required=True)],
        )
        request = self.builder.build(node, {"item-id": "123"}, self.base_url)
        assert "123" in request.url
        assert "{itemId}" not in request.url

    def test_query_params_included(self) -> None:
        node = make_command_node(
            "GET",
            "/items",
            query_params=["limit", "offset"],
            flags=[
                FlagDef(name="limit", type=FlagType.INTEGER),
                FlagDef(name="offset", type=FlagType.INTEGER),
            ],
        )
        request = self.builder.build(node, {"limit": 10, "offset": 0}, self.base_url)
        assert request.params.get("limit") == 10
        assert request.params.get("offset") == 0

    def test_header_params_included(self) -> None:
        node = make_command_node(
            "GET",
            "/items",
            header_params=["X-Request-Id"],
            flags=[FlagDef(name="x-request-id", type=FlagType.STRING)],
        )
        request = self.builder.build(node, {"x-request-id": "abc-123"}, self.base_url)
        assert "X-Request-Id" in request.headers

    def test_json_body_parsed(self) -> None:
        node = make_command_node(
            "POST",
            "/items",
            body_param="body",
            flags=[FlagDef(name="body", type=FlagType.JSON)],
        )
        request = self.builder.build(node, {"body": '{"name": "test"}'}, self.base_url)
        assert request.body == {"name": "test"}

    def test_base_url_trailing_slash_handled(self) -> None:
        node = make_command_node("GET", "/items")
        request = self.builder.build(node, {}, "https://api.example.com/")
        assert request.url == "https://api.example.com/items"

    def test_raises_without_execution(self) -> None:
        node = CommandNode(name="test", path=["test"], is_group=False)
        with pytest.raises(ValueError, match="no execution"):
            self.builder.build(node, {}, self.base_url)


class TestBuildCurlCommand:
    def test_simple_get(self) -> None:
        request = ApiRequest(method="GET", url="https://api.example.com/items")
        curl = build_curl_command(request)
        assert "curl" in curl
        assert "GET" in curl
        assert "https://api.example.com/items" in curl

    def test_with_headers(self) -> None:
        request = ApiRequest(
            method="GET",
            url="https://api.example.com/items",
            headers={"Authorization": "Bearer token"},
        )
        curl = build_curl_command(request)
        assert "Authorization" in curl

    def test_with_body(self) -> None:
        request = ApiRequest(
            method="POST",
            url="https://api.example.com/items",
            body={"name": "test"},
        )
        curl = build_curl_command(request)
        assert "-d" in curl

    def test_with_query_params(self) -> None:
        request = ApiRequest(
            method="GET",
            url="https://api.example.com/items",
            params={"limit": 10},
        )
        curl = build_curl_command(request)
        assert "limit=10" in curl
