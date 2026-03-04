from __future__ import annotations

import os
from collections.abc import Callable

from api2cli.errors import AuthError
from api2cli.models.config import AuthConfig, Credential, SpecConfig
from api2cli.models.runtime import ApiRequest
from api2cli.models.spec import SecuritySchemeType, SecuritySchemeDef
from api2cli.plugins.auth.api_key import ApiKeyAuthProvider
from api2cli.plugins.auth.basic_auth import BasicAuthProvider
from api2cli.plugins.auth.bearer import BearerAuthProvider
from api2cli.plugins.auth.credential_store import CredentialStore

_PROVIDERS = [BearerAuthProvider(), ApiKeyAuthProvider(), BasicAuthProvider()]

_ENV_VARS: dict[str, str] = {
    "bearer": "API2CLI_TOKEN",
    "apikey": "API2CLI_API_KEY",
    "basic": "API2CLI_BASIC_AUTH",
}


def _scheme_env_var(scheme: SecuritySchemeDef) -> str | None:
    """Return the environment variable name for a scheme, if any."""
    if scheme.type == SecuritySchemeType.HTTP:
        stype = (scheme.scheme or "").lower()
        return _ENV_VARS.get(stype)
    if scheme.type == SecuritySchemeType.API_KEY:
        return _ENV_VARS.get("apikey")
    return None


def _resolve_value(
    scheme: SecuritySchemeDef,
    cli_flags: dict[str, str],
    config: SpecConfig | None,
    store: CredentialStore,
) -> str | None:
    """Resolve credential value using priority order.

    Resolution order:
    1. CLI flags (--auth-token, --api-key, --basic-auth)
    2. Environment variables
    3. Credential store (via config credential_ref or scheme key)
    """
    # 1. CLI flags
    if scheme.type == SecuritySchemeType.HTTP and (scheme.scheme or "").lower() == "bearer":
        if val := cli_flags.get("auth_token") or cli_flags.get("auth-token"):
            return val
    if scheme.type == SecuritySchemeType.API_KEY:
        if val := cli_flags.get("api_key") or cli_flags.get("api-key"):
            return val
    if scheme.type == SecuritySchemeType.HTTP and (scheme.scheme or "").lower() == "basic":
        if val := cli_flags.get("basic_auth") or cli_flags.get("basic-auth"):
            return val

    # 2. Environment variables
    env_var = _scheme_env_var(scheme)
    if env_var and (val := os.environ.get(env_var)):
        return val

    # 3. Credential store
    ref = (config.base_url or scheme.name_key) if config else scheme.name_key
    credential = store.get(ref)
    if credential:
        return _extract_from_credential(credential, scheme)

    return None


def _extract_from_credential(credential: Credential, scheme: SecuritySchemeDef) -> str | None:
    """Extract the relevant value from a stored Credential."""
    auth = credential.auth_config
    if scheme.type == SecuritySchemeType.HTTP:
        stype = (scheme.scheme or "").lower()
        if stype == "bearer":
            return auth.token
        if stype == "basic":
            if auth.username and auth.password:
                return f"{auth.username}:{auth.password}"
    if scheme.type == SecuritySchemeType.API_KEY:
        return auth.key_value
    return None


class AuthResolver:
    """Resolves and applies authentication to API requests.

    Checks CLI flags, environment variables, and the credential store in
    priority order, then applies the matching auth provider.

    Args:
        store: Optional credential store. A default store is created if omitted.
    """

    def __init__(self, store: CredentialStore | None = None) -> None:
        self._store = store or CredentialStore()

    def resolve(
        self,
        security_schemes: dict[str, SecuritySchemeDef],
        security_requirements: list[dict[str, list[str]]],
        cli_flags: dict[str, str],
        config: SpecConfig | None = None,
    ) -> Callable[[ApiRequest], ApiRequest]:
        """Build a function that applies auth to a request.

        Args:
            security_schemes: Security scheme definitions from the API spec.
            security_requirements: Security requirements for the operation.
            cli_flags: Parsed CLI flag values (e.g. {"auth_token": "tok123"}).
            config: Optional spec config (used for credential_ref lookup).

        Returns:
            A callable that takes an ApiRequest and returns an authenticated one.

        Raises:
            AuthError: If auth is required but no credentials can be resolved.
        """
        if not security_requirements:
            return lambda req: req

        # Find first resolvable requirement set (OR logic between requirements)
        for requirement in security_requirements:
            patches: list[tuple[SecuritySchemeDef, str]] = []
            all_resolved = True

            for scheme_name in requirement:
                scheme = security_schemes.get(scheme_name)
                if scheme is None:
                    all_resolved = False
                    break

                value = _resolve_value(scheme, cli_flags, config, self._store)
                if value is None:
                    all_resolved = False
                    break

                patches.append((scheme, value))

            if all_resolved:
                captured = patches

                def _apply(req: ApiRequest, _patches: list = captured) -> ApiRequest:
                    for scheme, value in _patches:
                        for provider in _PROVIDERS:
                            if provider.applies_to(scheme):
                                req = provider.apply(req, scheme, value)
                                break
                    return req

                return _apply

        scheme_names = list(security_requirements[0].keys()) if security_requirements else []
        raise AuthError(
            f"Authentication required but no credentials found for: {', '.join(scheme_names)}. "
            "Provide --auth-token, --api-key, or run 'api2cli auth set' first."
        )
