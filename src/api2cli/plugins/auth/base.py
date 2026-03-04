from __future__ import annotations

from typing import Protocol

from api2cli.models.runtime import ApiRequest
from api2cli.models.spec import SecuritySchemeDef


class AuthProvider(Protocol):
    """Protocol for authentication providers.

    Auth providers read credentials from various sources and apply them
    to outgoing API requests.
    """

    def applies_to(self, scheme: SecuritySchemeDef) -> bool:
        """Return True if this provider handles the given security scheme."""
        ...

    def apply(self, request: ApiRequest, scheme: SecuritySchemeDef, value: str) -> ApiRequest:
        """Apply authentication to an API request.

        Args:
            request: The request to authenticate.
            scheme: The security scheme definition from the spec.
            value: The credential value (token, key, etc.).

        Returns:
            A new ApiRequest with auth applied.
        """
        ...
