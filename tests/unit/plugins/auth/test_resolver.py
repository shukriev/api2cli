from __future__ import annotations

import os
from pathlib import Path

import pytest

from api2cli.errors import AuthError
from api2cli.models.config import AuthConfig, Credential
from api2cli.models.runtime import ApiRequest
from api2cli.models.spec import ParameterLocation, SecuritySchemeType, SecuritySchemeDef
from api2cli.plugins.auth.credential_store import CredentialStore
from api2cli.plugins.auth.resolver import AuthResolver


def _make_request() -> ApiRequest:
    return ApiRequest(method="GET", url="https://api.example.com/data")


def _make_bearer_scheme() -> SecuritySchemeDef:
    return SecuritySchemeDef(name_key="bearerAuth", type=SecuritySchemeType.HTTP, scheme="bearer")


def _make_apikey_scheme() -> SecuritySchemeDef:
    return SecuritySchemeDef(
        name_key="apiKeyAuth",
        type=SecuritySchemeType.API_KEY,
        name="X-API-Key",
        in_=ParameterLocation.HEADER,
    )


class TestAuthResolver:
    def test_no_security_requirements_passes_through(self) -> None:
        resolver = AuthResolver()
        apply_fn = resolver.resolve(
            security_schemes={},
            security_requirements=[],
            cli_flags={},
        )
        request = _make_request()
        result = apply_fn(request)
        assert result.headers == {}

    def test_cli_flag_takes_precedence(self, tmp_path: Path) -> None:
        store = CredentialStore(path=tmp_path / "creds.json")
        store.set(
            "bearerAuth",
            Credential(
                api_id="bearerAuth",
                auth_config=AuthConfig(type="bearer", token="store-token"),
            ),
        )
        resolver = AuthResolver(store=store)
        scheme = _make_bearer_scheme()
        apply_fn = resolver.resolve(
            security_schemes={"bearerAuth": scheme},
            security_requirements=[{"bearerAuth": []}],
            cli_flags={"auth_token": "cli-token"},
        )
        result = apply_fn(_make_request())
        assert result.headers["Authorization"] == "Bearer cli-token"

    def test_env_var_takes_precedence_over_store(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        store = CredentialStore(path=tmp_path / "creds.json")
        store.set(
            "bearerAuth",
            Credential(
                api_id="bearerAuth",
                auth_config=AuthConfig(type="bearer", token="store-token"),
            ),
        )
        monkeypatch.setenv("API2CLI_TOKEN", "env-token")
        resolver = AuthResolver(store=store)
        scheme = _make_bearer_scheme()
        apply_fn = resolver.resolve(
            security_schemes={"bearerAuth": scheme},
            security_requirements=[{"bearerAuth": []}],
            cli_flags={},
        )
        result = apply_fn(_make_request())
        assert result.headers["Authorization"] == "Bearer env-token"

    def test_store_used_as_fallback(self, tmp_path: Path) -> None:
        store = CredentialStore(path=tmp_path / "creds.json")
        store.set(
            "bearerAuth",
            Credential(
                api_id="bearerAuth",
                auth_config=AuthConfig(type="bearer", token="store-token"),
            ),
        )
        resolver = AuthResolver(store=store)
        scheme = _make_bearer_scheme()
        apply_fn = resolver.resolve(
            security_schemes={"bearerAuth": scheme},
            security_requirements=[{"bearerAuth": []}],
            cli_flags={},
        )
        result = apply_fn(_make_request())
        assert result.headers["Authorization"] == "Bearer store-token"

    def test_missing_auth_raises_auth_error(self, tmp_path: Path) -> None:
        store = CredentialStore(path=tmp_path / "creds.json")
        resolver = AuthResolver(store=store)
        scheme = _make_bearer_scheme()
        with pytest.raises(AuthError, match="Authentication required"):
            resolver.resolve(
                security_schemes={"bearerAuth": scheme},
                security_requirements=[{"bearerAuth": []}],
                cli_flags={},
            )

    def test_api_key_resolved_from_cli_flag(self, tmp_path: Path) -> None:
        store = CredentialStore(path=tmp_path / "creds.json")
        resolver = AuthResolver(store=store)
        scheme = _make_apikey_scheme()
        apply_fn = resolver.resolve(
            security_schemes={"apiKeyAuth": scheme},
            security_requirements=[{"apiKeyAuth": []}],
            cli_flags={"api_key": "my-key"},
        )
        result = apply_fn(_make_request())
        assert result.headers["X-API-Key"] == "my-key"

    def test_api_key_resolved_from_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        store = CredentialStore(path=tmp_path / "creds.json")
        monkeypatch.setenv("API2CLI_API_KEY", "env-api-key")
        resolver = AuthResolver(store=store)
        scheme = _make_apikey_scheme()
        apply_fn = resolver.resolve(
            security_schemes={"apiKeyAuth": scheme},
            security_requirements=[{"apiKeyAuth": []}],
            cli_flags={},
        )
        result = apply_fn(_make_request())
        assert result.headers["X-API-Key"] == "env-api-key"
