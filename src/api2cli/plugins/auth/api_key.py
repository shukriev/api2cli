from __future__ import annotations

from api2cli.models.runtime import ApiRequest
from api2cli.models.spec import ParameterLocation, SecuritySchemeType, SecuritySchemeDef


class ApiKeyAuthProvider:
    """Authentication provider for API key schemes.

    Applies the API key to the request in the location specified
    by the security scheme (header, query, or cookie).
    """

    def applies_to(self, scheme: SecuritySchemeDef) -> bool:
        return scheme.type == SecuritySchemeType.API_KEY

    def apply(self, request: ApiRequest, scheme: SecuritySchemeDef, value: str) -> ApiRequest:
        """Apply the API key to the request.

        Args:
            request: The request to authenticate.
            scheme: The apiKey security scheme definition.
            value: The API key value.

        Returns:
            A new ApiRequest with the API key applied.
        """
        key_name = scheme.name or "X-API-Key"
        location = scheme.in_ or ParameterLocation.HEADER

        if location == ParameterLocation.HEADER:
            headers = {**request.headers, key_name: value}
            return request.model_copy(update={"headers": headers})
        elif location == ParameterLocation.QUERY:
            params = {**request.params, key_name: value}
            return request.model_copy(update={"params": params})
        elif location == ParameterLocation.COOKIE:
            existing_cookie = request.headers.get("Cookie", "")
            cookie_part = f"{key_name}={value}"
            new_cookie = f"{existing_cookie}; {cookie_part}" if existing_cookie else cookie_part
            headers = {**request.headers, "Cookie": new_cookie}
            return request.model_copy(update={"headers": headers})

        return request
