from __future__ import annotations

from api2cli.models.runtime import ApiRequest
from api2cli.models.spec import SecuritySchemeType, SecuritySchemeDef


class BearerAuthProvider:
    """Authentication provider for HTTP Bearer token schemes.

    Applies the token as an Authorization: Bearer <token> header.
    """

    def applies_to(self, scheme: SecuritySchemeDef) -> bool:
        return (
            scheme.type == SecuritySchemeType.HTTP
            and (scheme.scheme or "").lower() == "bearer"
        )

    def apply(self, request: ApiRequest, scheme: SecuritySchemeDef, value: str) -> ApiRequest:
        """Apply the Bearer token to the Authorization header.

        Args:
            request: The request to authenticate.
            scheme: The HTTP Bearer security scheme definition.
            value: The bearer token value.

        Returns:
            A new ApiRequest with the Authorization header set.
        """
        headers = {**request.headers, "Authorization": f"Bearer {value}"}
        return request.model_copy(update={"headers": headers})
