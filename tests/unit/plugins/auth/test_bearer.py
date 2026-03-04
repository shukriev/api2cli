from __future__ import annotations

from api2cli.models.runtime import ApiRequest
from api2cli.models.spec import SecuritySchemeType, SecuritySchemeDef
from api2cli.plugins.auth.bearer import BearerAuthProvider


def _make_bearer_scheme() -> SecuritySchemeDef:
    return SecuritySchemeDef(
        name_key="bearerAuth",
        type=SecuritySchemeType.HTTP,
        scheme="bearer",
    )


def _make_request() -> ApiRequest:
    return ApiRequest(method="GET", url="https://api.example.com/users")


class TestBearerAuthProvider:
    def test_applies_to_bearer_scheme(self) -> None:
        provider = BearerAuthProvider()
        scheme = _make_bearer_scheme()
        assert provider.applies_to(scheme) is True

    def test_does_not_apply_to_basic_scheme(self) -> None:
        provider = BearerAuthProvider()
        scheme = SecuritySchemeDef(
            name_key="basicAuth",
            type=SecuritySchemeType.HTTP,
            scheme="basic",
        )
        assert provider.applies_to(scheme) is False

    def test_does_not_apply_to_api_key_scheme(self) -> None:
        provider = BearerAuthProvider()
        scheme = SecuritySchemeDef(
            name_key="apiKey",
            type=SecuritySchemeType.API_KEY,
        )
        assert provider.applies_to(scheme) is False

    def test_token_applied_as_bearer_header(self) -> None:
        provider = BearerAuthProvider()
        scheme = _make_bearer_scheme()
        request = _make_request()
        result = provider.apply(request, scheme, "mytoken123")
        assert result.headers["Authorization"] == "Bearer mytoken123"

    def test_bearer_case_insensitive(self) -> None:
        provider = BearerAuthProvider()
        scheme = SecuritySchemeDef(
            name_key="bearerAuth",
            type=SecuritySchemeType.HTTP,
            scheme="Bearer",
        )
        assert provider.applies_to(scheme) is True

    def test_original_request_not_mutated(self) -> None:
        provider = BearerAuthProvider()
        scheme = _make_bearer_scheme()
        request = _make_request()
        provider.apply(request, scheme, "tok")
        assert "Authorization" not in request.headers
