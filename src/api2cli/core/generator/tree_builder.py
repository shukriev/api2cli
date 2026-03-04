from __future__ import annotations

from api2cli.core.generator.flag_generator import FlagGenerator
from api2cli.core.generator.help_generator import HelpGenerator
from api2cli.models.analyzed import AnalyzedSpec, OperationDef, ResourceDef
from api2cli.models.commands import (
    CommandNode,
    CommandTree,
    ExecutionDef,
    FlagDef,
    FlagType,
    OutputFormat,
    PaginationDef,
    PaginationStyle,
    TreeMeta,
)
from api2cli.models.spec import ParameterLocation

GLOBAL_FLAGS: list[FlagDef] = [
    FlagDef(
        name="output",
        short="o",
        type=FlagType.STRING,
        description="Output format",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.JSON.value,
    ),
    FlagDef(
        name="verbose",
        type=FlagType.BOOLEAN,
        description="Enable verbose output",
        default=False,
    ),
    FlagDef(
        name="dry-run",
        type=FlagType.BOOLEAN,
        description="Print request without executing",
        default=False,
    ),
    FlagDef(
        name="all",
        type=FlagType.BOOLEAN,
        description="Fetch all pages",
        default=False,
    ),
    FlagDef(
        name="page",
        type=FlagType.INTEGER,
        description="Page number",
        default=1,
    ),
    FlagDef(
        name="limit",
        type=FlagType.INTEGER,
        description="Items per page",
        default=100,
    ),
]


def _build_execution_def(operation: OperationDef) -> ExecutionDef:
    endpoint = operation.endpoint

    path_params = [
        p.name
        for p in endpoint.parameters
        if p.location == ParameterLocation.PATH
    ]
    query_params = [
        p.name
        for p in endpoint.parameters
        if p.location == ParameterLocation.QUERY
    ]
    header_params = [
        p.name
        for p in endpoint.parameters
        if p.location == ParameterLocation.HEADER
    ]

    # Determine body handling
    body_param: str | None = None
    body_fields: list[str] = []
    if endpoint.request_body:
        body_param = "body"

    # Auth schemes from spec
    auth_schemes: list[str] = []
    for security_req in endpoint.security:
        auth_schemes.extend(security_req.keys())

    return ExecutionDef(
        method=endpoint.method.value.upper(),
        url_template=endpoint.path,
        path_params=path_params,
        query_params=query_params,
        header_params=header_params,
        body_param=body_param,
        body_fields=body_fields,
        auth_schemes=auth_schemes,
        security_requirements=endpoint.security,
    )


def _build_pagination_def(operation: OperationDef) -> PaginationDef:
    params = {p.name.lower() for p in operation.endpoint.parameters}

    if "cursor" in params or "after" in params or "before" in params:
        cursor_param = next(
            (
                p.name
                for p in operation.endpoint.parameters
                if p.name.lower() in ("cursor", "after", "before")
            ),
            None,
        )
        return PaginationDef(style=PaginationStyle.CURSOR, cursor_param=cursor_param)

    if "offset" in params or "skip" in params:
        limit_param = next(
            (
                p.name
                for p in operation.endpoint.parameters
                if p.name.lower() in ("limit", "take", "size")
            ),
            None,
        )
        return PaginationDef(
            style=PaginationStyle.OFFSET,
            page_param=next(
                (
                    p.name
                    for p in operation.endpoint.parameters
                    if p.name.lower() in ("offset", "skip")
                ),
                None,
            ),
            limit_param=limit_param,
        )

    if "page" in params or "page_number" in params:
        return PaginationDef(
            style=PaginationStyle.PAGE,
            page_param="page",
            limit_param=next(
                (
                    p.name
                    for p in operation.endpoint.parameters
                    if p.name.lower() in ("limit", "per_page", "page_size")
                ),
                None,
            ),
        )

    return PaginationDef(style=PaginationStyle.NONE)


class TreeBuilder:
    """Builds a CommandTree from an AnalyzedSpec."""

    def __init__(self) -> None:
        self._flag_gen = FlagGenerator()
        self._help_gen = HelpGenerator()

    def build(self, analyzed: AnalyzedSpec) -> CommandTree:
        spec = analyzed.original_spec
        meta = TreeMeta(
            global_flags=GLOBAL_FLAGS,
            base_urls=[s.url for s in spec.servers],
            default_output=OutputFormat.JSON,
            api_title=spec.info.title,
            api_version=spec.info.version,
            security_schemes=spec.security_schemes,
        )

        root = CommandNode(name="root", is_group=True)

        for resource in analyzed.resources:
            self._add_resource_commands(root, resource)

        return CommandTree(
            meta=meta,
            root=root,
            spec_source=None,
        )

    def _add_resource_commands(
        self,
        parent: CommandNode,
        resource: ResourceDef,
    ) -> None:
        resource_name = resource.name

        if resource_name not in parent.children:
            parent.children[resource_name] = CommandNode(
                name=resource_name,
                path=self._get_path(parent) + [resource_name],
                description=resource.description or f"{resource_name} commands",
                is_group=True,
            )

        resource_node = parent.children[resource_name]

        for operation in resource.operations:
            cmd_name = operation.cli_name
            cmd_path = resource_node.path + [cmd_name]

            flags = self._flag_gen.generate(
                operation.endpoint.parameters,
                operation.endpoint.request_body,
            )
            execution = _build_execution_def(operation)
            pagination = _build_pagination_def(operation)
            description = self._help_gen.generate_description(operation)
            examples = self._help_gen.generate_examples(
                operation,
                " ".join(cmd_path),
            )

            cmd_node = CommandNode(
                name=cmd_name,
                path=cmd_path,
                description=description,
                flags=flags,
                execution=execution,
                pagination=pagination,
                examples=examples,
                is_group=False,
                deprecated=operation.endpoint.deprecated,
            )

            resource_node.children[cmd_name] = cmd_node

        for child_resource in resource.children:
            self._add_resource_commands(resource_node, child_resource)

    def _get_path(self, node: CommandNode) -> list[str]:
        return node.path if node.name != "root" else []
