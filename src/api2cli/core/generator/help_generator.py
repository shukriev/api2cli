from __future__ import annotations

from api2cli.models.analyzed import CrudOperation, OperationDef

_CRUD_HELP_TEMPLATES: dict[CrudOperation, str] = {
    CrudOperation.LIST: "List {resource}",
    CrudOperation.GET: "Get a {resource} by ID",
    CrudOperation.CREATE: "Create a new {resource}",
    CrudOperation.UPDATE: "Update a {resource}",
    CrudOperation.PATCH: "Partially update a {resource}",
    CrudOperation.DELETE: "Delete a {resource}",
    CrudOperation.ACTION: "Perform {action} on {resource}",
}


class HelpGenerator:
    """Generates help text and examples for commands."""

    def generate_description(self, operation: OperationDef) -> str:
        """Generate a description for a command node.

        Args:
            operation: The analyzed operation.

        Returns:
            Human-readable description string.
        """
        # Prefer the spec's summary/description
        if operation.endpoint.summary:
            return operation.endpoint.summary
        if operation.endpoint.description:
            # Take the first sentence
            desc = operation.endpoint.description.split(".")[0].strip()
            return desc or self._template_description(operation)
        return self._template_description(operation)

    def _template_description(self, operation: OperationDef) -> str:
        """Generate a templated description for an operation.

        Args:
            operation: The analyzed operation.

        Returns:
            A templated description string.
        """
        resource_name = operation.resource_name.replace("-", " ")
        template = _CRUD_HELP_TEMPLATES.get(
            operation.crud_operation, "Execute {resource} action"
        )
        return template.format(
            resource=resource_name,
            action=operation.cli_name,
        )

    def generate_examples(self, operation: OperationDef, command_path: str) -> list[str]:
        """Generate example usage strings.

        Args:
            operation: The analyzed operation.
            command_path: The full CLI command path (e.g., "pets list").

        Returns:
            List of example command strings.
        """
        examples: list[str] = []
        base = f"api2cli run {command_path}"

        if operation.crud_operation == CrudOperation.LIST:
            examples.append(f"{base} --limit 10")
        elif operation.crud_operation == CrudOperation.GET:
            # Find path params
            path_params = [
                p.name
                for p in operation.endpoint.parameters
                if p.location.value == "path"
            ]
            if path_params:
                param_str = " ".join(f"--{p} <{p}>" for p in path_params)
                examples.append(f"{base} {param_str}")
            else:
                examples.append(base)
        elif operation.crud_operation == CrudOperation.CREATE:
            examples.append(f"{base} --body '{{\"key\": \"value\"}}'")
        else:
            examples.append(base)

        return examples
