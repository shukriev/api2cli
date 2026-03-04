from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from api2cli.models.spec import ApiSpec, EndpointDef


class CrudOperation(StrEnum):
    """CRUD operation types."""

    LIST = "list"
    GET = "get"
    CREATE = "create"
    UPDATE = "update"
    PATCH = "patch"
    DELETE = "delete"
    ACTION = "action"


class ResourceType(StrEnum):
    """Resource type classification."""

    COLLECTION = "collection"
    SINGLETON = "singleton"
    ACTION = "action"
    NESTED = "nested"


class OperationDef(BaseModel):
    """A single analyzed operation with CLI metadata."""

    endpoint: EndpointDef
    crud_operation: CrudOperation
    resource_path: list[str] = Field(default_factory=list)
    cli_name: str = ""
    resource_name: str = ""
    parent_resource: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


class ResourceDef(BaseModel):
    """A detected API resource with its operations."""

    name: str
    path_prefix: str
    resource_type: ResourceType = ResourceType.COLLECTION
    operations: list[OperationDef] = Field(default_factory=list)
    children: list[ResourceDef] = Field(default_factory=list)
    description: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


class ResourceTreeNode(BaseModel):
    """Node in the resource tree."""

    name: str
    resource: ResourceDef | None = None
    children: dict[str, ResourceTreeNode] = Field(default_factory=dict)


class AnalyzedSpec(BaseModel):
    """Result of analyzing an ApiSpec."""

    original_spec: ApiSpec
    resources: list[ResourceDef] = Field(default_factory=list)
    resource_tree: ResourceTreeNode = Field(
        default_factory=lambda: ResourceTreeNode(name="root")
    )
    warnings: list[str] = Field(default_factory=list)
    extensions: dict[str, Any] = Field(default_factory=dict)
