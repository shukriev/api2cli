from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from api2cli.models.commands import CommandNode, CommandTree, FlagDef, FlagType


class RoutingError(Exception):
    """Raised when command routing fails."""


@dataclass
class ParsedCommand:
    """Result of routing and parsing a command invocation."""

    node: CommandNode
    flag_values: dict[str, Any] = field(default_factory=dict)
    remaining: list[str] = field(default_factory=list)


def _parse_flag_value(value_str: str, flag: FlagDef) -> Any:
    """Parse a flag value string to the appropriate Python type."""
    if flag.type == FlagType.INTEGER:
        return int(value_str)
    if flag.type == FlagType.FLOAT:
        return float(value_str)
    if flag.type == FlagType.BOOLEAN:
        return value_str.lower() in ("true", "1", "yes")
    return value_str


class CommandRouter:
    """Routes CLI args through a CommandTree and validates flags.

    Parses a list of string arguments against the command tree to find
    the target command node and extract flag values.
    """

    def route(
        self,
        tree: CommandTree,
        args: list[str],
    ) -> ParsedCommand:
        """Route args through the tree and return the matched command + flags.

        Args:
            tree: The command tree.
            args: List of CLI argument strings (after the spec flag).

        Returns:
            ParsedCommand with the matched node and parsed flags.

        Raises:
            RoutingError: If no command matches or required flags are missing.
        """
        node = tree.root
        consumed = 0

        # Navigate through command path
        for i, arg in enumerate(args):
            if arg.startswith("-"):
                break
            if arg in node.children:
                node = node.children[arg]
                consumed = i + 1
            else:
                break

        if node.is_group:
            available = list(node.children.keys())
            raise RoutingError(
                f"Command '{node.name}' is a group. "
                f"Available subcommands: {', '.join(available)}"
            )

        # Parse flags
        flag_map = {f.name: f for f in node.flags}
        short_map = {f.short: f for f in node.flags if f.short}

        flag_values: dict[str, Any] = {}
        remaining_args = args[consumed:]
        i = 0
        while i < len(remaining_args):
            arg = remaining_args[i]
            if not arg.startswith("-"):
                i += 1
                continue

            # Strip leading dashes
            flag_name = arg[2:] if arg.startswith("--") else arg[1:]

            # Handle --flag=value syntax
            flag_value_inline: str | None = None
            if "=" in flag_name:
                flag_name, flag_value_inline = flag_name.split("=", 1)

            # Look up flag definition
            flag_def = flag_map.get(flag_name) or short_map.get(flag_name)
            if flag_def is None:
                # Unknown flag - skip with its value
                i += 1
                if flag_value_inline is None and i < len(remaining_args) and not remaining_args[i].startswith("-"):
                    i += 1
                continue

            # Get value
            if flag_def.type == FlagType.BOOLEAN and flag_value_inline is None:
                # Boolean flag without value = True
                flag_values[flag_def.name] = True
            else:
                if flag_value_inline is not None:
                    value_str = flag_value_inline
                elif i + 1 < len(remaining_args) and not remaining_args[i + 1].startswith("-"):
                    i += 1
                    value_str = remaining_args[i]
                else:
                    value_str = ""
                flag_values[flag_def.name] = _parse_flag_value(value_str, flag_def)

            i += 1

        # Apply defaults for missing flags
        for flag_def in node.flags:
            if flag_def.name not in flag_values and flag_def.default is not None:
                flag_values[flag_def.name] = flag_def.default

        # Validate required flags
        missing = [
            f.name for f in node.flags
            if f.required and f.name not in flag_values
        ]
        if missing:
            raise RoutingError(f"Missing required flags: {', '.join(missing)}")

        return ParsedCommand(node=node, flag_values=flag_values)
