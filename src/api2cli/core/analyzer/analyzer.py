from __future__ import annotations

from api2cli.core.analyzer.resource_detector import ResourceDetector
from api2cli.errors import Err, Ok, Result
from api2cli.models.analyzed import AnalyzedSpec
from api2cli.models.spec import ApiSpec


class DefaultAnalyzer:
    """Default implementation of the spec analyzer.

    Orchestrates resource detection, CRUD detection, and naming to
    produce an AnalyzedSpec from an ApiSpec.
    """

    def __init__(self) -> None:
        self._resource_detector = ResourceDetector()

    def analyze(self, spec: ApiSpec) -> Result[AnalyzedSpec]:
        """Analyze an ApiSpec into an AnalyzedSpec.

        Args:
            spec: The normalized API spec to analyze.

        Returns:
            Ok(AnalyzedSpec) on success, Err(AnalysisError) on failure.
        """
        from api2cli.errors import AnalysisError

        try:
            resources, resource_tree = self._resource_detector.detect(spec)

            warnings: list[str] = []
            # Warn about endpoints without operationId
            for endpoint in spec.endpoints:
                if not endpoint.operation_id:
                    warnings.append(
                        f"Endpoint {endpoint.method.value.upper()} {endpoint.path} "
                        "has no operationId; using path-based naming."
                    )

            analyzed = AnalyzedSpec(
                original_spec=spec,
                resources=resources,
                resource_tree=resource_tree,
                warnings=warnings,
            )
            return Ok(analyzed)
        except Exception as exc:
            return Err(AnalysisError(f"Analysis failed: {exc}"))
