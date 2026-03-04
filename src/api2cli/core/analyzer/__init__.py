from __future__ import annotations

from api2cli.core.analyzer.analyzer import DefaultAnalyzer
from api2cli.core.analyzer.crud_detector import detect_operations, detect_verb
from api2cli.core.analyzer.naming_engine import (
    get_short_flag,
    operation_id_to_path,
    path_to_resource_name,
    strip_api_prefix,
    to_kebab_case,
    to_snake_case,
)
from api2cli.core.analyzer.resource_detector import ResourceDetector

__all__ = [
    "DefaultAnalyzer",
    "ResourceDetector",
    "detect_verb",
    "detect_operations",
    "get_short_flag",
    "operation_id_to_path",
    "path_to_resource_name",
    "strip_api_prefix",
    "to_kebab_case",
    "to_snake_case",
]
