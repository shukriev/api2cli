from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SpecFormat(StrEnum):
    """Supported API spec formats."""

    OPENAPI = "openapi"
    GRAPHQL = "graphql"
    HAR = "har"
    UNKNOWN = "unknown"


class HttpMethod(StrEnum):
    """HTTP methods."""

    GET = "get"
    POST = "post"
    PUT = "put"
    PATCH = "patch"
    DELETE = "delete"
    HEAD = "head"
    OPTIONS = "options"
    TRACE = "trace"


class ParameterLocation(StrEnum):
    """Parameter locations in HTTP requests."""

    PATH = "path"
    QUERY = "query"
    HEADER = "header"
    COOKIE = "cookie"


class SecuritySchemeType(StrEnum):
    """Security scheme types."""

    API_KEY = "apiKey"
    HTTP = "http"
    OAUTH2 = "oauth2"
    OPENID_CONNECT = "openIdConnect"


class OAuthFlowType(StrEnum):
    """OAuth2 flow types."""

    IMPLICIT = "implicit"
    PASSWORD = "password"
    CLIENT_CREDENTIALS = "clientCredentials"
    AUTHORIZATION_CODE = "authorizationCode"


class SchemaDef(BaseModel):
    """JSON Schema definition for a parameter or body."""

    type: str | None = None
    format: str | None = None
    title: str | None = None
    description: str | None = None
    default: Any = None
    example: Any = None
    enum: list[Any] | None = None
    items: SchemaDef | None = None
    properties: dict[str, SchemaDef] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)
    additional_properties: bool | SchemaDef | None = None
    all_of: list[SchemaDef] = Field(default_factory=list, alias="allOf")
    one_of: list[SchemaDef] = Field(default_factory=list, alias="oneOf")
    any_of: list[SchemaDef] = Field(default_factory=list, alias="anyOf")
    ref: str | None = Field(default=None, alias="$ref")
    nullable: bool = False
    minimum: float | None = None
    maximum: float | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class ParameterDef(BaseModel):
    """Definition of an API parameter."""

    name: str
    location: ParameterLocation
    required: bool = False
    description: str | None = None
    schema_def: SchemaDef | None = Field(default=None)
    example: Any = None
    deprecated: bool = False
    style: str | None = None
    explode: bool | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


class RequestBodyDef(BaseModel):
    """Definition of a request body."""

    description: str | None = None
    required: bool = False
    content: dict[str, SchemaDef] = Field(default_factory=dict)
    extensions: dict[str, Any] = Field(default_factory=dict)


class ResponseDef(BaseModel):
    """Definition of an API response."""

    status_code: str
    description: str | None = None
    content: dict[str, SchemaDef] = Field(default_factory=dict)
    headers: dict[str, SchemaDef] = Field(default_factory=dict)
    extensions: dict[str, Any] = Field(default_factory=dict)


class OAuthFlow(BaseModel):
    """OAuth2 flow definition."""

    authorization_url: str | None = None
    token_url: str | None = None
    refresh_url: str | None = None
    scopes: dict[str, str] = Field(default_factory=dict)


class OAuthFlows(BaseModel):
    """OAuth2 flows definition."""

    implicit: OAuthFlow | None = None
    password: OAuthFlow | None = None
    client_credentials: OAuthFlow | None = Field(default=None)
    authorization_code: OAuthFlow | None = Field(default=None)


class SecuritySchemeDef(BaseModel):
    """Definition of a security scheme."""

    name_key: str
    type: SecuritySchemeType
    description: str | None = None
    name: str | None = None
    in_: ParameterLocation | None = Field(default=None)
    scheme: str | None = None
    bearer_format: str | None = None
    flows: OAuthFlows | None = None
    open_id_connect_url: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


class ServerVariable(BaseModel):
    """Server variable definition."""

    default: str
    enum: list[str] = Field(default_factory=list)
    description: str | None = None


class ServerDef(BaseModel):
    """Server definition."""

    url: str
    description: str | None = None
    variables: dict[str, ServerVariable] = Field(default_factory=dict)
    extensions: dict[str, Any] = Field(default_factory=dict)


class TagDef(BaseModel):
    """API tag definition."""

    name: str
    description: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


class EndpointDef(BaseModel):
    """Definition of a single API endpoint."""

    path: str
    method: HttpMethod
    operation_id: str | None = None
    summary: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    parameters: list[ParameterDef] = Field(default_factory=list)
    request_body: RequestBodyDef | None = None
    responses: list[ResponseDef] = Field(default_factory=list)
    security: list[dict[str, list[str]]] = Field(default_factory=list)
    deprecated: bool = False
    extensions: dict[str, Any] = Field(default_factory=dict)


class ApiInfo(BaseModel):
    """API metadata."""

    title: str
    version: str
    description: str | None = None
    terms_of_service: str | None = None
    contact: dict[str, str] = Field(default_factory=dict)
    license: dict[str, str] = Field(default_factory=dict)
    extensions: dict[str, Any] = Field(default_factory=dict)


class ApiSpec(BaseModel):
    """Normalized API specification."""

    info: ApiInfo
    servers: list[ServerDef] = Field(default_factory=list)
    endpoints: list[EndpointDef] = Field(default_factory=list)
    security_schemes: dict[str, SecuritySchemeDef] = Field(default_factory=dict)
    tags: list[TagDef] = Field(default_factory=list)
    format: SpecFormat = SpecFormat.OPENAPI
    raw_version: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)
