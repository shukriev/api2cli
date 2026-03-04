from __future__ import annotations

import re
from collections import defaultdict

from api2cli.core.analyzer.crud_detector import detect_verb
from api2cli.core.analyzer.naming_engine import (
    operation_id_to_path,
    strip_api_prefix,
    to_kebab_case,
)
from api2cli.models.analyzed import (
    CrudOperation,
    OperationDef,
    ResourceDef,
    ResourceTreeNode,
    ResourceType,
)
from api2cli.models.spec import ApiSpec

_PATH_PARAM_PATTERN = re.compile(r"\{[^}]+\}")


def _extract_resource_segments(path: str) -> list[str]:
    """Extract resource name segments from a path.

    Strips path parameters and common prefixes.

    Args:
        path: URL path like /pets/{petId}/vaccines/{vaccineId}

    Returns:
        List of resource segments like ["pets", "vaccines"]
    """
    clean_path = strip_api_prefix(path)
    segments = [s for s in clean_path.split("/") if s]
    # Keep only non-parameter segments
    resource_segs = [s for s in segments if not _PATH_PARAM_PATTERN.match(s)]
    return resource_segs


def _build_resource_path(path: str) -> list[str]:
    """Build the resource path list from a URL path.

    Args:
        path: URL path like /projects/{id}/tasks

    Returns:
        List like ["projects", "tasks"]
    """
    segs = _extract_resource_segments(path)
    return [to_kebab_case(s) for s in segs]


def _infer_from_path(path: str, method_verb: CrudOperation) -> tuple[list[str], str]:
    """Infer resource path and CLI name from URL path + verb.

    Args:
        path: URL path like /pets/{petId}
        method_verb: Detected CRUD operation.

    Returns:
        Tuple of (resource_path, cli_name)
    """
    resource_path = _build_resource_path(path)
    if not resource_path:
        return (["unknown"], method_verb.value)
    return (resource_path, method_verb.value)


def _infer_from_operation_id(operation_id: str) -> tuple[list[str], str]:
    """Infer resource path and CLI name from operationId.

    Args:
        operation_id: OpenAPI operationId like listProjectTasks.

    Returns:
        Tuple of (resource_path, cli_name) like (["projects", "tasks"], "list")
    """
    parts = operation_id_to_path(operation_id)
    if len(parts) < 2:
        return ([parts[0]] if parts else ["unknown"], "action")
    return (parts[:-1], parts[-1])


class ResourceDetector:
    """Detects API resources from an ApiSpec.

    Groups endpoints by resource path and creates ResourceDef objects.
    """

    def detect(self, spec: ApiSpec) -> tuple[list[ResourceDef], ResourceTreeNode]:
        """Detect resources from an ApiSpec.

        Args:
            spec: The normalized API spec.

        Returns:
            Tuple of (resource_list, resource_tree_root).
        """
        resource_groups: dict[tuple[str, ...], list[OperationDef]] = defaultdict(list)

        for endpoint in spec.endpoints:
            crud_op = detect_verb(endpoint)

            # Always use path-based resource grouping for consistency.
            # The path is the authoritative source for resource identity
            # (e.g., /pets and /pets/{id} both belong to the "pets" resource).
            # Use operation_id only for the CLI verb name.
            resource_path, _path_cli_name = _infer_from_path(endpoint.path, crud_op)

            if endpoint.operation_id:
                _, cli_name = _infer_from_operation_id(endpoint.operation_id)
            else:
                cli_name = _path_cli_name

            op = OperationDef(
                endpoint=endpoint,
                crud_operation=crud_op,
                resource_path=resource_path,
                cli_name=cli_name,
                resource_name=resource_path[-1] if resource_path else "unknown",
                parent_resource=resource_path[-2] if len(resource_path) > 1 else None,
            )

            resource_key = tuple(resource_path)
            resource_groups[resource_key].append(op)

        resources: list[ResourceDef] = []
        for resource_path_key, ops in sorted(resource_groups.items()):
            path_prefix = "/" + "/".join(resource_path_key)
            resource_name = resource_path_key[-1] if resource_path_key else "unknown"

            resource_type = ResourceType.COLLECTION
            if len(resource_path_key) > 1:
                resource_type = ResourceType.NESTED

            resource = ResourceDef(
                name=resource_name,
                path_prefix=path_prefix,
                resource_type=resource_type,
                operations=ops,
            )
            resources.append(resource)

        root = ResourceTreeNode(name="root")
        for resource in resources:
            node = root
            resource_key = tuple(
                resource.operations[0].resource_path if resource.operations else [resource.name]
            )
            for i, segment in enumerate(resource_key):
                if segment not in node.children:
                    node.children[segment] = ResourceTreeNode(name=segment)
                child = node.children[segment]
                if i == len(resource_key) - 1:
                    child.resource = resource
                node = child

        return resources, root
