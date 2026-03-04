from __future__ import annotations

from api2cli.models.spec import (
    ApiInfo,
    ApiSpec,
    EndpointDef,
    HttpMethod,
    ParameterDef,
    ParameterLocation,
    ResponseDef,
    SchemaDef,
    ServerDef,
    SpecFormat,
    TagDef,
)


def make_schema(type_: str = "string", **kwargs: object) -> SchemaDef:
    """Create a SchemaDef for testing.

    Args:
        type_: The schema type string.
        **kwargs: Additional keyword arguments passed to SchemaDef.

    Returns:
        A SchemaDef instance.
    """
    return SchemaDef(type=type_, **kwargs)


def make_parameter(
    name: str,
    location: ParameterLocation = ParameterLocation.QUERY,
    required: bool = False,
    type_: str = "string",
) -> ParameterDef:
    """Create a ParameterDef for testing.

    Args:
        name: The parameter name.
        location: The parameter location.
        required: Whether the parameter is required.
        type_: The parameter schema type.

    Returns:
        A ParameterDef instance.
    """
    return ParameterDef(
        name=name,
        location=location,
        required=required,
        schema_def=make_schema(type_),
    )


def make_endpoint(
    path: str = "/items",
    method: HttpMethod = HttpMethod.GET,
    operation_id: str | None = None,
    tags: list[str] | None = None,
    parameters: list[ParameterDef] | None = None,
    summary: str | None = None,
) -> EndpointDef:
    """Create an EndpointDef for testing.

    Args:
        path: The endpoint path.
        method: The HTTP method.
        operation_id: The operation ID.
        tags: The tags for the endpoint.
        parameters: The parameters for the endpoint.
        summary: A short summary.

    Returns:
        An EndpointDef instance.
    """
    return EndpointDef(
        path=path,
        method=method,
        operation_id=operation_id,
        tags=tags or [],
        parameters=parameters or [],
        summary=summary,
        responses=[
            ResponseDef(
                status_code="200",
                description="Success",
                content={"application/json": make_schema("object")},
            )
        ],
    )


def make_api_spec(
    title: str = "Test API",
    version: str = "1.0.0",
    base_url: str = "https://api.example.com",
    endpoints: list[EndpointDef] | None = None,
    tags: list[str] | None = None,
) -> ApiSpec:
    """Create an ApiSpec for testing.

    Args:
        title: The API title.
        version: The API version string.
        base_url: The base URL for the API server.
        endpoints: List of endpoints to include.
        tags: List of tag names.

    Returns:
        An ApiSpec instance.
    """
    tag_defs = [TagDef(name=t) for t in (tags or [])]
    return ApiSpec(
        info=ApiInfo(title=title, version=version),
        servers=[ServerDef(url=base_url)],
        endpoints=endpoints or [],
        tags=tag_defs,
        format=SpecFormat.OPENAPI,
        raw_version="3.0.3",
    )


def make_petstore_spec() -> ApiSpec:
    """Create a petstore-like ApiSpec for testing.

    Returns:
        An ApiSpec instance modeled after the Petstore API.
    """
    endpoints = [
        make_endpoint(
            path="/pets",
            method=HttpMethod.GET,
            operation_id="listPets",
            tags=["pets"],
            parameters=[
                make_parameter("limit", ParameterLocation.QUERY, type_="integer"),
                make_parameter("offset", ParameterLocation.QUERY, type_="integer"),
            ],
            summary="List all pets",
        ),
        make_endpoint(
            path="/pets",
            method=HttpMethod.POST,
            operation_id="createPet",
            tags=["pets"],
            summary="Create a pet",
        ),
        make_endpoint(
            path="/pets/{petId}",
            method=HttpMethod.GET,
            operation_id="getPet",
            tags=["pets"],
            parameters=[
                make_parameter("petId", ParameterLocation.PATH, required=True)
            ],
            summary="Get a pet by ID",
        ),
        make_endpoint(
            path="/pets/{petId}",
            method=HttpMethod.PUT,
            operation_id="updatePet",
            tags=["pets"],
            parameters=[
                make_parameter("petId", ParameterLocation.PATH, required=True)
            ],
            summary="Update a pet",
        ),
        make_endpoint(
            path="/pets/{petId}",
            method=HttpMethod.DELETE,
            operation_id="deletePet",
            tags=["pets"],
            parameters=[
                make_parameter("petId", ParameterLocation.PATH, required=True)
            ],
            summary="Delete a pet",
        ),
        make_endpoint(
            path="/owners",
            method=HttpMethod.GET,
            operation_id="listOwners",
            tags=["owners"],
            summary="List all owners",
        ),
        make_endpoint(
            path="/owners/{ownerId}",
            method=HttpMethod.GET,
            operation_id="getOwner",
            tags=["owners"],
            parameters=[
                make_parameter("ownerId", ParameterLocation.PATH, required=True)
            ],
            summary="Get an owner",
        ),
    ]
    return make_api_spec(
        title="Petstore API",
        version="1.0.0",
        base_url="https://petstore.example.com",
        endpoints=endpoints,
        tags=["pets", "owners"],
    )
