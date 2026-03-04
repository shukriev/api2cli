from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from api2cli.models.spec import SecuritySchemeDef


class FlagType(StrEnum):
    """CLI flag value types."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    JSON = "json"


class OutputFormat(StrEnum):
    """Output format options."""

    JSON = "json"
    TABLE = "table"
    CSV = "csv"
    YAML = "yaml"
    NDJSON = "ndjson"
    AI = "ai"


class PaginationStyle(StrEnum):
    """Pagination strategy."""

    OFFSET = "offset"
    CURSOR = "cursor"
    PAGE = "page"
    LINK_HEADER = "link_header"
    NONE = "none"


class FlagDef(BaseModel):
    """Definition of a CLI flag."""

    name: str
    short: str | None = None
    type: FlagType = FlagType.STRING
    required: bool = False
    default: Any = None
    description: str | None = None
    choices: list[Any] | None = None
    multiple: bool = False
    hidden: bool = False
    extensions: dict[str, Any] = Field(default_factory=dict)


class PaginationDef(BaseModel):
    """Pagination configuration for a command."""

    style: PaginationStyle = PaginationStyle.NONE
    page_param: str | None = None
    limit_param: str | None = None
    cursor_param: str | None = None
    next_url_field: str | None = None
    total_field: str | None = None
    default_limit: int = 100
    extensions: dict[str, Any] = Field(default_factory=dict)


class ExecutionDef(BaseModel):
    """Execution details for a command."""

    method: str
    url_template: str
    path_params: list[str] = Field(default_factory=list)
    query_params: list[str] = Field(default_factory=list)
    header_params: list[str] = Field(default_factory=list)
    body_param: str | None = None
    body_fields: list[str] = Field(default_factory=list)
    auth_schemes: list[str] = Field(default_factory=list)
    security_requirements: list[dict[str, list[str]]] = Field(default_factory=list)
    content_type: str = "application/json"
    extensions: dict[str, Any] = Field(default_factory=dict)


class CommandNode(BaseModel):
    """A node in the command tree representing a CLI command or group."""

    name: str
    path: list[str] = Field(default_factory=list)
    description: str | None = None
    flags: list[FlagDef] = Field(default_factory=list)
    execution: ExecutionDef | None = None
    pagination: PaginationDef | None = None
    examples: list[str] = Field(default_factory=list)
    children: dict[str, CommandNode] = Field(default_factory=dict)
    is_group: bool = False
    deprecated: bool = False
    extensions: dict[str, Any] = Field(default_factory=dict)


class TreeMeta(BaseModel):
    """Metadata for the command tree."""

    global_flags: list[FlagDef] = Field(default_factory=list)
    base_urls: list[str] = Field(default_factory=list)
    default_output: OutputFormat = OutputFormat.JSON
    version: str = "0.1.0"
    api_title: str = ""
    api_version: str = ""
    security_schemes: dict[str, SecuritySchemeDef] = Field(default_factory=dict)
    extensions: dict[str, Any] = Field(default_factory=dict)


class CommandTree(BaseModel):
    """Full command tree for a CLI."""

    meta: TreeMeta = Field(default_factory=TreeMeta)
    root: CommandNode = Field(default_factory=lambda: CommandNode(name="root", is_group=True))
    spec_source: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)
