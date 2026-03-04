from __future__ import annotations

import pytest

from api2cli.models.spec import (
    ApiInfo,
    ApiSpec,
    EndpointDef,
    HttpMethod,
    SchemaDef,
    ServerDef,
    SpecFormat,
)


@pytest.fixture
def minimal_api_info() -> ApiInfo:
    """Minimal ApiInfo fixture."""
    return ApiInfo(title="Test API", version="1.0.0")


@pytest.fixture
def minimal_server() -> ServerDef:
    """Minimal ServerDef fixture."""
    return ServerDef(url="https://api.example.com")


@pytest.fixture
def string_schema() -> SchemaDef:
    """String SchemaDef fixture."""
    return SchemaDef(type="string")


@pytest.fixture
def minimal_endpoint() -> EndpointDef:
    """Minimal EndpointDef fixture."""
    return EndpointDef(
        path="/pets",
        method=HttpMethod.GET,
        operation_id="listPets",
        summary="List all pets",
    )


@pytest.fixture
def minimal_api_spec(minimal_api_info: ApiInfo, minimal_server: ServerDef) -> ApiSpec:
    """Minimal ApiSpec fixture."""
    return ApiSpec(
        info=minimal_api_info,
        servers=[minimal_server],
        format=SpecFormat.OPENAPI,
    )
