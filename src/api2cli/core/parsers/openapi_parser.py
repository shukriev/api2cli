from __future__ import annotations

import json
import logging
from typing import Any, Protocol

import yaml

from api2cli.errors import Err, Ok, ParseError
from api2cli.models.spec import (
    ApiInfo,
    ApiSpec,
    EndpointDef,
    HttpMethod,
    OAuthFlow,
    OAuthFlows,
    ParameterDef,
    ParameterLocation,
    RequestBodyDef,
    ResponseDef,
    SchemaDef,
    SecuritySchemeDef,
    SecuritySchemeType,
    ServerDef,
    ServerVariable,
    SpecFormat,
    TagDef,
)

logger = logging.getLogger(__name__)

# Type alias
type Result[T] = Ok[T] | Err[T]

SUPPORTED_VERSIONS = {"3.0", "3.1"}


class SpecParser(Protocol):
    """Protocol for spec parsers."""

    def parse(self, content: str, source: str = "<string>") -> Result[ApiSpec]:
        """Parse raw spec content into an ApiSpec.

        Args:
            content: Raw spec content string.
            source: Source identifier for error messages.

        Returns:
            Ok(ApiSpec) on success, Err on failure.
        """
        ...

    def can_parse(self, content: str) -> bool:
        """Return True if this parser can handle the given content.

        Args:
            content: Raw spec content string.

        Returns:
            True if the parser can handle this content.
        """
        ...


def _load_raw(content: str) -> dict[str, Any]:
    """Load raw YAML or JSON content into a dict.

    Args:
        content: Raw spec content string.

    Returns:
        Parsed dict representation.
    """
    stripped = content.strip()
    if stripped.startswith("{"):
        return json.loads(stripped)  # type: ignore[no-any-return]
    return yaml.safe_load(stripped)  # type: ignore[no-any-return]


def _parse_schema(raw: dict[str, Any] | None) -> SchemaDef:
    """Parse a raw schema dict into a SchemaDef.

    Args:
        raw: Raw schema dict or None.

    Returns:
        A SchemaDef instance.
    """
    if raw is None:
        return SchemaDef()

    properties: dict[str, SchemaDef] = {}
    for prop_name, prop_schema in raw.get("properties", {}).items():
        properties[prop_name] = _parse_schema(prop_schema)

    items: SchemaDef | None = None
    if "items" in raw:
        items = _parse_schema(raw["items"])

    all_of = [_parse_schema(s) for s in raw.get("allOf", [])]
    one_of = [_parse_schema(s) for s in raw.get("oneOf", [])]
    any_of = [_parse_schema(s) for s in raw.get("anyOf", [])]

    additional_props = raw.get("additionalProperties")
    additional_properties: bool | SchemaDef | None = None
    if isinstance(additional_props, bool):
        additional_properties = additional_props
    elif isinstance(additional_props, dict):
        additional_properties = _parse_schema(additional_props)

    extensions = {k: v for k, v in raw.items() if k.startswith("x-")}

    return SchemaDef(
        type=raw.get("type"),
        format=raw.get("format"),
        title=raw.get("title"),
        description=raw.get("description"),
        default=raw.get("default"),
        example=raw.get("example"),
        enum=raw.get("enum"),
        items=items,
        properties=properties,
        required=raw.get("required", []),
        additional_properties=additional_properties,
        allOf=all_of,
        oneOf=one_of,
        anyOf=any_of,
        **{"$ref": raw.get("$ref")},
        nullable=raw.get("nullable", False),
        minimum=raw.get("minimum"),
        maximum=raw.get("maximum"),
        min_length=raw.get("minLength"),
        max_length=raw.get("maxLength"),
        pattern=raw.get("pattern"),
        extensions=extensions,
    )


def _parse_parameter(raw: dict[str, Any]) -> ParameterDef:
    """Parse a raw parameter dict into a ParameterDef.

    Args:
        raw: Raw parameter dict.

    Returns:
        A ParameterDef instance.
    """
    location_str = raw.get("in", "query")
    try:
        location = ParameterLocation(location_str)
    except ValueError:
        location = ParameterLocation.QUERY

    schema_def: SchemaDef | None = None
    if "schema" in raw:
        schema_def = _parse_schema(raw["schema"])

    extensions = {k: v for k, v in raw.items() if k.startswith("x-")}

    return ParameterDef(
        name=raw.get("name", ""),
        location=location,
        required=raw.get("required", location == ParameterLocation.PATH),
        description=raw.get("description"),
        schema_def=schema_def,
        example=raw.get("example"),
        deprecated=raw.get("deprecated", False),
        style=raw.get("style"),
        explode=raw.get("explode"),
        extensions=extensions,
    )


def _parse_request_body(raw: dict[str, Any]) -> RequestBodyDef:
    """Parse a raw requestBody dict into a RequestBodyDef.

    Args:
        raw: Raw requestBody dict.

    Returns:
        A RequestBodyDef instance.
    """
    content: dict[str, SchemaDef] = {}
    for media_type, media_obj in raw.get("content", {}).items():
        if isinstance(media_obj, dict) and "schema" in media_obj:
            content[media_type] = _parse_schema(media_obj["schema"])
        else:
            content[media_type] = SchemaDef()

    extensions = {k: v for k, v in raw.items() if k.startswith("x-")}

    return RequestBodyDef(
        description=raw.get("description"),
        required=raw.get("required", False),
        content=content,
        extensions=extensions,
    )


def _parse_response(status_code: str, raw: dict[str, Any]) -> ResponseDef:
    """Parse a raw response dict into a ResponseDef.

    Args:
        status_code: HTTP status code string.
        raw: Raw response dict.

    Returns:
        A ResponseDef instance.
    """
    content: dict[str, SchemaDef] = {}
    for media_type, media_obj in raw.get("content", {}).items():
        if isinstance(media_obj, dict) and "schema" in media_obj:
            content[media_type] = _parse_schema(media_obj["schema"])
        else:
            content[media_type] = SchemaDef()

    headers: dict[str, SchemaDef] = {}
    for header_name, header_obj in raw.get("headers", {}).items():
        if isinstance(header_obj, dict) and "schema" in header_obj:
            headers[header_name] = _parse_schema(header_obj["schema"])

    extensions = {k: v for k, v in raw.items() if k.startswith("x-")}

    return ResponseDef(
        status_code=status_code,
        description=raw.get("description"),
        content=content,
        headers=headers,
        extensions=extensions,
    )


def _parse_server(raw: dict[str, Any]) -> ServerDef:
    """Parse a raw server dict into a ServerDef.

    Args:
        raw: Raw server dict.

    Returns:
        A ServerDef instance.
    """
    variables: dict[str, ServerVariable] = {}
    for var_name, var_obj in raw.get("variables", {}).items():
        if isinstance(var_obj, dict):
            variables[var_name] = ServerVariable(
                default=str(var_obj.get("default", "")),
                enum=[str(e) for e in var_obj.get("enum", [])],
                description=var_obj.get("description"),
            )

    extensions = {k: v for k, v in raw.items() if k.startswith("x-")}

    return ServerDef(
        url=raw.get("url", ""),
        description=raw.get("description"),
        variables=variables,
        extensions=extensions,
    )


def _parse_oauth_flow(raw: dict[str, Any]) -> OAuthFlow:
    """Parse a raw OAuth flow dict into an OAuthFlow.

    Args:
        raw: Raw OAuth flow dict.

    Returns:
        An OAuthFlow instance.
    """
    return OAuthFlow(
        authorization_url=raw.get("authorizationUrl"),
        token_url=raw.get("tokenUrl"),
        refresh_url=raw.get("refreshUrl"),
        scopes=raw.get("scopes", {}),
    )


def _parse_security_scheme(name_key: str, raw: dict[str, Any]) -> SecuritySchemeDef:
    """Parse a raw security scheme dict into a SecuritySchemeDef.

    Args:
        name_key: The scheme's key name in the securitySchemes map.
        raw: Raw security scheme dict.

    Returns:
        A SecuritySchemeDef instance.
    """
    try:
        scheme_type = SecuritySchemeType(raw.get("type", "apiKey"))
    except ValueError:
        scheme_type = SecuritySchemeType.API_KEY

    in_location: ParameterLocation | None = None
    if "in" in raw:
        try:
            in_location = ParameterLocation(raw["in"])
        except ValueError:
            in_location = None

    flows: OAuthFlows | None = None
    if "flows" in raw:
        flows_raw = raw["flows"]
        flows = OAuthFlows(
            implicit=_parse_oauth_flow(flows_raw["implicit"]) if "implicit" in flows_raw else None,
            password=_parse_oauth_flow(flows_raw["password"]) if "password" in flows_raw else None,
            client_credentials=(
                _parse_oauth_flow(flows_raw["clientCredentials"])
                if "clientCredentials" in flows_raw
                else None
            ),
            authorization_code=(
                _parse_oauth_flow(flows_raw["authorizationCode"])
                if "authorizationCode" in flows_raw
                else None
            ),
        )

    extensions = {k: v for k, v in raw.items() if k.startswith("x-")}

    return SecuritySchemeDef(
        name_key=name_key,
        type=scheme_type,
        description=raw.get("description"),
        name=raw.get("name"),
        in_=in_location,
        scheme=raw.get("scheme"),
        bearer_format=raw.get("bearerFormat"),
        flows=flows,
        open_id_connect_url=raw.get("openIdConnectUrl"),
        extensions=extensions,
    )


def _parse_endpoint(
    path: str,
    method: str,
    operation: dict[str, Any],
    path_params: list[ParameterDef],
) -> EndpointDef | None:
    """Parse a single endpoint definition.

    Args:
        path: The URL path string.
        method: The HTTP method string.
        operation: Raw operation dict.
        path_params: Parameters defined at the path item level.

    Returns:
        An EndpointDef instance, or None if the method is unrecognized.
    """
    try:
        http_method = HttpMethod(method.lower())
    except ValueError:
        return None

    op_params: list[ParameterDef] = []
    param_names: set[str] = set()
    for raw_param in operation.get("parameters", []):
        param = _parse_parameter(raw_param)
        op_params.append(param)
        param_names.add(param.name)

    merged_params = list(op_params)
    for path_param in path_params:
        if path_param.name not in param_names:
            merged_params.append(path_param)

    request_body: RequestBodyDef | None = None
    if "requestBody" in operation:
        request_body = _parse_request_body(operation["requestBody"])

    responses: list[ResponseDef] = []
    for status_code, raw_response in operation.get("responses", {}).items():
        if isinstance(raw_response, dict):
            responses.append(_parse_response(str(status_code), raw_response))

    security: list[dict[str, list[str]]] = operation.get("security", [])

    extensions = {k: v for k, v in operation.items() if k.startswith("x-")}

    return EndpointDef(
        path=path,
        method=http_method,
        operation_id=operation.get("operationId"),
        summary=operation.get("summary"),
        description=operation.get("description"),
        tags=operation.get("tags", []),
        parameters=merged_params,
        request_body=request_body,
        responses=responses,
        security=security,
        deprecated=operation.get("deprecated", False),
        extensions=extensions,
    )


class OpenApiParser:
    """Parser for OpenAPI 3.0 and 3.1 specifications.

    Parses OpenAPI JSON or YAML specs into normalized ApiSpec objects.
    Does not resolve $refs (that is handled in Iteration 8).
    """

    def can_parse(self, content: str) -> bool:
        """Return True if this content looks like an OpenAPI spec.

        Args:
            content: Raw spec content string.

        Returns:
            True if the content appears to be an OpenAPI spec.
        """
        try:
            data = _load_raw(content)
            return isinstance(data, dict) and ("openapi" in data or "swagger" in data)
        except Exception:
            return False

    def parse(self, content: str, source: str = "<string>") -> Result[ApiSpec]:
        """Parse OpenAPI spec content into an ApiSpec.

        Args:
            content: Raw OpenAPI JSON or YAML content.
            source: Source identifier (file path or URL) for error messages.

        Returns:
            Ok(ApiSpec) on success, Err(ParseError) on failure.
        """
        try:
            data = _load_raw(content)
        except Exception as exc:
            return Err(ParseError(f"Failed to parse spec from {source}: {exc}"))

        if not isinstance(data, dict):
            return Err(ParseError(f"Spec at {source} is not a valid mapping"))

        openapi_version = data.get("openapi", data.get("swagger", ""))
        if not openapi_version:
            return Err(
                ParseError(f"Spec at {source} has no 'openapi' or 'swagger' version field")
            )

        major_minor = ".".join(str(openapi_version).split(".")[:2])
        if major_minor not in SUPPORTED_VERSIONS and not str(openapi_version).startswith("2."):
            logger.warning(
                "Unsupported OpenAPI version %s in %s, proceeding anyway",
                openapi_version,
                source,
            )

        raw_info = data.get("info", {})
        if not isinstance(raw_info, dict):
            return Err(ParseError(f"Spec at {source} has invalid 'info' section"))

        info_extensions = {k: v for k, v in raw_info.items() if k.startswith("x-")}
        info = ApiInfo(
            title=raw_info.get("title", "Untitled API"),
            version=str(raw_info.get("version", "0.0.0")),
            description=raw_info.get("description"),
            terms_of_service=raw_info.get("termsOfService"),
            contact=raw_info.get("contact", {}),
            license=raw_info.get("license", {}),
            extensions=info_extensions,
        )

        servers: list[ServerDef] = []
        for raw_server in data.get("servers", []):
            if isinstance(raw_server, dict):
                servers.append(_parse_server(raw_server))

        if not servers:
            servers = [ServerDef(url="/")]

        security_schemes: dict[str, SecuritySchemeDef] = {}
        components = data.get("components", {})
        if isinstance(components, dict):
            raw_schemes = components.get("securitySchemes", {})
            if isinstance(raw_schemes, dict):
                for scheme_name, raw_scheme in raw_schemes.items():
                    if isinstance(raw_scheme, dict):
                        security_schemes[scheme_name] = _parse_security_scheme(
                            scheme_name, raw_scheme
                        )

        tags: list[TagDef] = []
        for raw_tag in data.get("tags", []):
            if isinstance(raw_tag, dict):
                tag_extensions = {k: v for k, v in raw_tag.items() if k.startswith("x-")}
                tags.append(
                    TagDef(
                        name=raw_tag.get("name", ""),
                        description=raw_tag.get("description"),
                        extensions=tag_extensions,
                    )
                )

        endpoints: list[EndpointDef] = []
        paths = data.get("paths", {})
        if isinstance(paths, dict):
            for path, path_item in paths.items():
                if not isinstance(path_item, dict):
                    continue

                path_level_params: list[ParameterDef] = []
                for raw_param in path_item.get("parameters", []):
                    if isinstance(raw_param, dict):
                        path_level_params.append(_parse_parameter(raw_param))

                for method in [
                    "get",
                    "post",
                    "put",
                    "patch",
                    "delete",
                    "head",
                    "options",
                    "trace",
                ]:
                    operation = path_item.get(method)
                    if not isinstance(operation, dict):
                        continue

                    endpoint = _parse_endpoint(path, method, operation, path_level_params)
                    if endpoint is not None:
                        endpoints.append(endpoint)

        extensions = {k: v for k, v in data.items() if k.startswith("x-")}

        spec = ApiSpec(
            info=info,
            servers=servers,
            endpoints=endpoints,
            security_schemes=security_schemes,
            tags=tags,
            format=SpecFormat.OPENAPI,
            raw_version=str(openapi_version),
            extensions=extensions,
        )

        return Ok(spec)
