from __future__ import annotations

import pytest

from api2cli.models.runtime import ApiRequest
from api2cli.models.spec import ParameterLocation, SecuritySchemeType, SecuritySchemeDef
from api2cli.plugins.auth.api_key import ApiKeyAuthProvider


def _make_scheme(location: ParameterLocation, name: str = "X-API-Key") -> SecuritySchemeDef:
    return SecuritySchemeDef(
        name_key="apiKey",
        type=SecuritySchemeType.API_KEY,
        name=name,
        in_=location,
    )


def _make_request() -> ApiRequest:
    return ApiRequest(method="GET", url="https://api.example.com/pets")


class TestApiKeyAuthProvider:
    def test_applies_to_api_key_scheme(self) -> None:
        provider = ApiKeyAuthProvider()
        scheme = _make_scheme(ParameterLocation.HEADER)
        assert provider.applies_to(scheme) is True

    def test_does_not_apply_to_http_scheme(self) -> None:
        provider = ApiKeyAuthProvider()
        scheme = SecuritySchemeDef(
            name_key="bearer",
            type=SecuritySchemeType.HTTP,
            scheme="bearer",
        )
        assert provider.applies_to(scheme) is False

    def test_key_applied_to_header(self) -> None:
        provider = ApiKeyAuthProvider()
        scheme = _make_scheme(ParameterLocation.HEADER, "X-API-Key")
        request = _make_request()
        result = provider.apply(request, scheme, "secret-key")
        assert result.headers["X-API-Key"] == "secret-key"

    def test_key_applied_to_query(self) -> None:
        provider = ApiKeyAuthProvider()
        scheme = _make_scheme(ParameterLocation.QUERY, "api_key")
        request = _make_request()
        result = provider.apply(request, scheme, "qkey")
        assert result.params["api_key"] == "qkey"

    def test_key_applied_to_cookie(self) -> None:
        provider = ApiKeyAuthProvider()
        scheme = _make_scheme(ParameterLocation.COOKIE, "session")
        request = _make_request()
        result = provider.apply(request, scheme, "abc123")
        assert "session=abc123" in result.headers["Cookie"]

    def test_cookie_appended_to_existing_cookie(self) -> None:
        provider = ApiKeyAuthProvider()
        scheme = _make_scheme(ParameterLocation.COOKIE, "session")
        request = ApiRequest(
            method="GET",
            url="https://api.example.com/pets",
            headers={"Cookie": "existing=value"},
        )
        result = provider.apply(request, scheme, "abc123")
        assert "existing=value" in result.headers["Cookie"]
        assert "session=abc123" in result.headers["Cookie"]

    def test_original_request_not_mutated(self) -> None:
        provider = ApiKeyAuthProvider()
        scheme = _make_scheme(ParameterLocation.HEADER)
        request = _make_request()
        provider.apply(request, scheme, "key")
        assert "X-API-Key" not in request.headers
