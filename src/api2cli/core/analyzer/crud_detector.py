from __future__ import annotations

import re

from api2cli.models.analyzed import CrudOperation
from api2cli.models.spec import EndpointDef, HttpMethod

_METHOD_CRUD: dict[HttpMethod, CrudOperation] = {
    HttpMethod.GET: CrudOperation.LIST,  # Default, may be overridden
    HttpMethod.POST: CrudOperation.CREATE,
    HttpMethod.PUT: CrudOperation.UPDATE,
    HttpMethod.PATCH: CrudOperation.PATCH,
    HttpMethod.DELETE: CrudOperation.DELETE,
    HttpMethod.HEAD: CrudOperation.ACTION,
    HttpMethod.OPTIONS: CrudOperation.ACTION,
    HttpMethod.TRACE: CrudOperation.ACTION,
}

_PATH_PARAM_PATTERN = re.compile(r"\{[^}]+\}")


def _has_path_param_at_end(path: str) -> bool:
    """Return True if the path ends with a path parameter."""
    segments = path.rstrip("/").split("/")
    return bool(segments) and bool(_PATH_PARAM_PATTERN.match(segments[-1]))


def detect_verb(endpoint: EndpointDef) -> CrudOperation:
    """Detect the CRUD verb for an endpoint.

    Uses HTTP method and path structure to determine the operation type.
    For GET: GET /resource → list, GET /resource/{id} → get.

    Args:
        endpoint: The endpoint to analyze.

    Returns:
        The detected CrudOperation.
    """
    method = endpoint.method

    if method == HttpMethod.GET:
        if _has_path_param_at_end(endpoint.path):
            return CrudOperation.GET
        return CrudOperation.LIST

    return _METHOD_CRUD.get(method, CrudOperation.ACTION)


def detect_operations(endpoints: list[EndpointDef]) -> dict[str, CrudOperation]:
    """Detect CRUD operations for a list of endpoints.

    Args:
        endpoints: List of endpoints to analyze.

    Returns:
        Dict mapping operation_id (or path+method) to CrudOperation.
    """
    result: dict[str, CrudOperation] = {}
    for endpoint in endpoints:
        key = endpoint.operation_id or f"{endpoint.method.value}:{endpoint.path}"
        result[key] = detect_verb(endpoint)
    return result
