from __future__ import annotations

import base64

from api2cli.models.runtime import ApiRequest
from api2cli.models.spec import SecuritySchemeType, SecuritySchemeDef


class BasicAuthProvider:
    """Authentication provider for HTTP Basic auth schemes.

    Applies base64-encoded username:password as Authorization: Basic <credentials>.
    """

    def applies_to(self, scheme: SecuritySchemeDef) -> bool:
        return (
            scheme.type == SecuritySchemeType.HTTP
            and (scheme.scheme or "").lower() == "basic"
        )

    def apply(self, request: ApiRequest, scheme: SecuritySchemeDef, value: str) -> ApiRequest:
        """Apply Basic auth credentials to the Authorization header.

        Args:
            request: The request to authenticate.
            scheme: The HTTP Basic security scheme definition.
            value: Credentials as "username:password" or pre-encoded base64.

        Returns:
            A new ApiRequest with the Authorization header set.
        """
        if ":" in value:
            encoded = base64.b64encode(value.encode()).decode()
        else:
            encoded = value
        headers = {**request.headers, "Authorization": f"Basic {encoded}"}
        return request.model_copy(update={"headers": headers})
