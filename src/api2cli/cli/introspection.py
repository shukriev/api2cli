from __future__ import annotations

import json
from typing import Any

from api2cli.models.commands import CommandNode, CommandTree


def _node_to_dict(node: CommandNode, include_flags: bool = True) -> dict[str, Any]:
    """Convert a CommandNode to a dict for JSON output."""
    result: dict[str, Any] = {
        "name": node.name,
        "path": node.path,
        "description": node.description,
        "is_group": node.is_group,
        "deprecated": node.deprecated,
    }
    if include_flags and not node.is_group:
        result["flags"] = [
            {
                "name": f.name,
                "short": f.short,
                "type": f.type.value,
                "required": f.required,
                "default": f.default,
                "description": f.description,
                "choices": f.choices,
            }
            for f in node.flags
        ]
    if node.execution:
        result["execution"] = {
            "method": node.execution.method,
            "url_template": node.execution.url_template,
        }
    if node.children:
        result["children"] = {
            name: _node_to_dict(child, include_flags=False)
            for name, child in node.children.items()
        }
    if node.examples:
        result["examples"] = node.examples
    return result


def capabilities_output(tree: CommandTree) -> str:
    """Serialize a CommandTree to a JSON capabilities string.

    Args:
        tree: The command tree to serialize.

    Returns:
        JSON string representing the tree capabilities.
    """
    output = {
        "api": {
            "title": tree.meta.api_title,
            "version": tree.meta.api_version,
            "base_urls": tree.meta.base_urls,
        },
        "global_flags": [
            {
                "name": f.name,
                "type": f.type.value,
                "description": f.description,
                "default": f.default,
            }
            for f in tree.meta.global_flags
        ],
        "commands": {
            name: _node_to_dict(child)
            for name, child in tree.root.children.items()
        },
    }
    return json.dumps(output, indent=2, default=str)


def describe_output(tree: CommandTree, command_path: str) -> str | None:
    """Find a command by its dot-notation path and return its JSON description.

    Args:
        tree: The command tree to search.
        command_path: Dot-notation path like "pets.list" or "pets list".

    Returns:
        JSON string with command details, or None if not found.
    """
    # Support both dot notation and space notation
    parts = command_path.replace(".", " ").split()

    node = tree.root
    for part in parts:
        if part in node.children:
            node = node.children[part]
        else:
            return None

    return json.dumps(_node_to_dict(node, include_flags=True), indent=2, default=str)
