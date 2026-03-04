from __future__ import annotations

import base64

from api2cli.models.runtime import ApiRequest
from api2cli.models.spec import SecuritySchemeType, SecuritySchemeDef
from api2cli.plugins.auth.basic_auth import BasicAuthProvider


def _make_basic_scheme() -> SecuritySchemeDef:
    return SecuritySchemeDef(
        name_key="basicAuth",
        type=SecuritySchemeType.HTTP,
        scheme="basic",
    )


def _make_request() -> ApiRequest:
    return ApiRequest(method="GET", url="https://api.example.com/users")


class TestBasicAuthProvider:
    def test_applies_to_basic_scheme(self) -> None:
        provider = BasicAuthProvider()
        scheme = _make_basic_scheme()
        assert provider.applies_to(scheme) is True

    def test_does_not_apply_to_bearer_scheme(self) -> None:
        provider = BasicAuthProvider()
        scheme = SecuritySchemeDef(
            name_key="bearerAuth",
            type=SecuritySchemeType.HTTP,
            scheme="bearer",
        )
        assert provider.applies_to(scheme) is False

    def test_username_password_encoded_correctly(self) -> None:
        provider = BasicAuthProvider()
        scheme = _make_basic_scheme()
        request = _make_request()
        result = provider.apply(request, scheme, "admin:secret")
        expected = base64.b64encode(b"admin:secret").decode()
        assert result.headers["Authorization"] == f"Basic {expected}"

    def test_pre_encoded_value_used_directly(self) -> None:
        provider = BasicAuthProvider()
        scheme = _make_basic_scheme()
        request = _make_request()
        encoded = base64.b64encode(b"user:pass").decode()
        result = provider.apply(request, scheme, encoded)
        assert result.headers["Authorization"] == f"Basic {encoded}"

    def test_original_request_not_mutated(self) -> None:
        provider = BasicAuthProvider()
        scheme = _make_basic_scheme()
        request = _make_request()
        provider.apply(request, scheme, "user:pass")
        assert "Authorization" not in request.headers
