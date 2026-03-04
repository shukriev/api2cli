from __future__ import annotations

from api2cli.core.generator.tree_builder import TreeBuilder
from api2cli.errors import Err, GenerationError, Ok, Result
from api2cli.models.analyzed import AnalyzedSpec
from api2cli.models.commands import CommandTree


class DefaultGenerator:
    """Default command tree generator.

    Orchestrates flag generation, help text generation, and tree building
    to produce a CommandTree from an AnalyzedSpec.
    """

    def __init__(self) -> None:
        self._tree_builder = TreeBuilder()

    def generate(self, analyzed: AnalyzedSpec) -> Result[CommandTree]:
        """Generate a CommandTree from an AnalyzedSpec.

        Args:
            analyzed: The analyzed API spec.

        Returns:
            Ok(CommandTree) on success, Err(GenerationError) on failure.
        """
        try:
            tree = self._tree_builder.build(analyzed)
            return Ok(tree)
        except Exception as exc:
            return Err(GenerationError(f"Failed to generate command tree: {exc}"))
