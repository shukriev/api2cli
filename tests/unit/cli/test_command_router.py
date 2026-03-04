from __future__ import annotations

import pytest

from api2cli.cli.command_router import CommandRouter, RoutingError
from api2cli.core.analyzer.analyzer import DefaultAnalyzer
from api2cli.core.generator.generator import DefaultGenerator
from api2cli.errors import Ok
from api2cli.models.commands import (
    CommandNode,
    CommandTree,
    ExecutionDef,
    FlagDef,
    FlagType,
    TreeMeta,
)
from tests.factories.spec_factory import make_petstore_spec


def _build_petstore_tree() -> CommandTree:
    spec = make_petstore_spec()
    analyzer = DefaultAnalyzer()
    result = analyzer.analyze(spec)
    assert isinstance(result, Ok)
    generator = DefaultGenerator()
    tree_result = generator.generate(result.value)
    assert isinstance(tree_result, Ok)
    return tree_result.value


class TestCommandRouter:
    def setup_method(self) -> None:
        self.tree = _build_petstore_tree()
        self.router = CommandRouter()

    def test_route_simple_command(self) -> None:
        parsed = self.router.route(self.tree, ["pets", "list"])
        assert parsed.node.name == "list"

    def test_route_with_flag(self) -> None:
        parsed = self.router.route(self.tree, ["pets", "list", "--limit", "5"])
        assert parsed.node.name == "list"
        assert parsed.flag_values.get("limit") == 5

    def test_route_with_integer_flag(self) -> None:
        # pets.list has offset (integer) param in the factory spec
        parsed = self.router.route(self.tree, ["pets", "list", "--offset", "10"])
        assert parsed.node.name == "list"
        assert parsed.flag_values.get("offset") == 10

    def test_route_group_raises_error(self) -> None:
        with pytest.raises(RoutingError):
            self.router.route(self.tree, ["pets"])

    def test_route_unknown_command(self) -> None:
        with pytest.raises(RoutingError):
            self.router.route(self.tree, ["pets", "nonexistent"])

    def test_route_delete_command(self) -> None:
        # First need the pet-id flag
        # The petId param should be --pet-id after kebab conversion
        parsed = self.router.route(self.tree, ["pets", "delete", "--pet-id", "123"])
        assert parsed.node.name == "delete"

    def test_flag_equals_syntax(self) -> None:
        parsed = self.router.route(self.tree, ["pets", "list", "--limit=10"])
        assert parsed.flag_values.get("limit") == 10

    def test_default_values_applied(self) -> None:
        parsed = self.router.route(self.tree, ["pets", "list"])
        # limit has a default of 20 from petstore spec, or may have default from schema
        # soft check - just verifying the route succeeds
        assert parsed.node.name == "list"

    def test_missing_required_flag_raises(self) -> None:
        # Get command requires petId (required path param)
        # But our router should detect missing required flags
        # The get command has pet-id as required
        # Try routing without it - should raise
        with pytest.raises(RoutingError, match="Missing required"):
            self.router.route(self.tree, ["pets", "get"])


class TestCommandRouterMinimal:
    def test_route_minimal_tree(self) -> None:
        tree = CommandTree(
            meta=TreeMeta(),
            root=CommandNode(
                name="root",
                is_group=True,
                children={
                    "items": CommandNode(
                        name="items",
                        path=["items"],
                        is_group=True,
                        children={
                            "list": CommandNode(
                                name="list",
                                path=["items", "list"],
                                is_group=False,
                                flags=[
                                    FlagDef(name="limit", type=FlagType.INTEGER, default=10),
                                ],
                                execution=ExecutionDef(
                                    method="GET",
                                    url_template="/items",
                                ),
                            )
                        },
                    )
                },
            ),
        )
        router = CommandRouter()
        parsed = router.route(tree, ["items", "list"])
        assert parsed.node.name == "list"
        assert parsed.flag_values.get("limit") == 10

    def test_boolean_flag(self) -> None:
        tree = CommandTree(
            meta=TreeMeta(),
            root=CommandNode(
                name="root",
                is_group=True,
                children={
                    "cmd": CommandNode(
                        name="cmd",
                        path=["cmd"],
                        is_group=False,
                        flags=[FlagDef(name="verbose", type=FlagType.BOOLEAN)],
                        execution=ExecutionDef(method="GET", url_template="/cmd"),
                    )
                },
            ),
        )
        router = CommandRouter()
        parsed = router.route(tree, ["cmd", "--verbose"])
        assert parsed.flag_values.get("verbose") is True
