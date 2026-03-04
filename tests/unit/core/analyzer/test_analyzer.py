from __future__ import annotations

import pytest

from api2cli.core.analyzer.analyzer import DefaultAnalyzer
from api2cli.core.analyzer.crud_detector import detect_operations, detect_verb
from api2cli.core.analyzer.naming_engine import (
    get_short_flag,
    operation_id_to_path,
    strip_api_prefix,
    to_kebab_case,
    to_snake_case,
)
from api2cli.errors import Ok
from api2cli.models.analyzed import CrudOperation
from api2cli.models.spec import HttpMethod
from tests.factories.spec_factory import make_api_spec, make_endpoint, make_petstore_spec


class TestNamingEngine:
    @pytest.mark.parametrize("path,expected", [
        ("/api/v1/pets", "/pets"),
        ("/api/v2/users", "/users"),
        ("/v1/resources", "/resources"),
        ("/api/items", "/items"),
        ("/pets", "/pets"),
        ("/api", "/"),
    ])
    def test_strip_api_prefix(self, path: str, expected: str) -> None:
        assert strip_api_prefix(path) == expected

    @pytest.mark.parametrize("name,expected", [
        ("petOwner", "pet-owner"),
        ("PetOwner", "pet-owner"),
        ("pet_owner", "pet-owner"),
        ("pet owner", "pet-owner"),
        ("listPets", "list-pets"),
        # APIKey: consecutive uppercase letters are not split by the regex
        # ([a-z\d])([A-Z]) only matches lowercase-to-uppercase transitions
        ("APIKey", "apikey"),
        ("simple", "simple"),
    ])
    def test_to_kebab_case(self, name: str, expected: str) -> None:
        assert to_kebab_case(name) == expected

    @pytest.mark.parametrize("name,expected", [
        ("pet-owner", "pet_owner"),
        ("list-pets", "list_pets"),
        ("simple", "simple"),
    ])
    def test_to_snake_case(self, name: str, expected: str) -> None:
        assert to_snake_case(name) == expected

    @pytest.mark.parametrize("operation_id,expected_verb", [
        ("listPets", "list"),
        ("getPet", "get"),
        ("createPet", "create"),
        ("updatePet", "update"),
        ("deletePet", "delete"),
        ("listProjectTasks", "list"),
        ("getProjectTask", "get"),
    ])
    def test_operation_id_to_path_verb(self, operation_id: str, expected_verb: str) -> None:
        parts = operation_id_to_path(operation_id)
        assert parts[-1] == expected_verb

    def test_operation_id_list_pets(self) -> None:
        parts = operation_id_to_path("listPets")
        assert "list" in parts
        assert "pets" in parts

    def test_operation_id_nested(self) -> None:
        parts = operation_id_to_path("listProjectTasks")
        assert parts[-1] == "list"
        assert len(parts) >= 2

    def test_get_short_flag_basic(self) -> None:
        taken: set[str] = set()
        short = get_short_flag("limit", taken)
        assert short == "l"

    def test_get_short_flag_skip_reserved(self) -> None:
        # h, v, o are reserved
        taken: set[str] = {"l"}
        short = get_short_flag("limit", taken)
        assert short != "h" and short != "v" and short != "o"

    def test_get_short_flag_taken(self) -> None:
        taken = {"l", "i", "m", "t"}
        short = get_short_flag("limit", taken)
        # Should find something or return None
        assert short is None or len(short) == 1


class TestCrudDetector:
    @pytest.mark.parametrize("method,path,expected", [
        (HttpMethod.GET, "/pets", CrudOperation.LIST),
        (HttpMethod.GET, "/pets/{petId}", CrudOperation.GET),
        (HttpMethod.POST, "/pets", CrudOperation.CREATE),
        (HttpMethod.PUT, "/pets/{petId}", CrudOperation.UPDATE),
        (HttpMethod.PATCH, "/pets/{petId}", CrudOperation.PATCH),
        (HttpMethod.DELETE, "/pets/{petId}", CrudOperation.DELETE),
        (HttpMethod.GET, "/api/v1/users", CrudOperation.LIST),
        (HttpMethod.GET, "/api/v1/users/{id}", CrudOperation.GET),
    ])
    def test_detect_verb(self, method: HttpMethod, path: str, expected: CrudOperation) -> None:
        endpoint = make_endpoint(path=path, method=method)
        assert detect_verb(endpoint) == expected

    def test_detect_operations_dict(self) -> None:
        endpoints = [
            make_endpoint("/pets", HttpMethod.GET, "listPets"),
            make_endpoint("/pets/{id}", HttpMethod.GET, "getPet"),
            make_endpoint("/pets", HttpMethod.POST, "createPet"),
        ]
        ops = detect_operations(endpoints)
        assert ops["listPets"] == CrudOperation.LIST
        assert ops["getPet"] == CrudOperation.GET
        assert ops["createPet"] == CrudOperation.CREATE


class TestDefaultAnalyzer:
    def test_analyze_petstore(self) -> None:
        spec = make_petstore_spec()
        analyzer = DefaultAnalyzer()
        result = analyzer.analyze(spec)
        assert isinstance(result, Ok)
        analyzed = result.value
        assert len(analyzed.resources) > 0

    def test_petstore_has_pets_resource(self) -> None:
        spec = make_petstore_spec()
        analyzer = DefaultAnalyzer()
        result = analyzer.analyze(spec)
        assert isinstance(result, Ok)
        analyzed = result.value
        resource_names = [r.name for r in analyzed.resources]
        assert "pets" in resource_names

    def test_petstore_has_owners_resource(self) -> None:
        spec = make_petstore_spec()
        analyzer = DefaultAnalyzer()
        result = analyzer.analyze(spec)
        assert isinstance(result, Ok)
        analyzed = result.value
        resource_names = [r.name for r in analyzed.resources]
        assert "owners" in resource_names

    def test_pets_resource_has_crud_operations(self) -> None:
        spec = make_petstore_spec()
        analyzer = DefaultAnalyzer()
        result = analyzer.analyze(spec)
        assert isinstance(result, Ok)
        analyzed = result.value
        pets = next(r for r in analyzed.resources if r.name == "pets")
        op_verbs = {op.crud_operation for op in pets.operations}
        assert CrudOperation.LIST in op_verbs
        assert CrudOperation.GET in op_verbs
        assert CrudOperation.CREATE in op_verbs
        assert CrudOperation.DELETE in op_verbs

    def test_analyze_empty_spec(self) -> None:
        spec = make_api_spec()
        analyzer = DefaultAnalyzer()
        result = analyzer.analyze(spec)
        assert isinstance(result, Ok)
        analyzed = result.value
        assert analyzed.resources == []

    def test_warnings_for_missing_operation_id(self) -> None:
        endpoint = make_endpoint("/pets", HttpMethod.GET)  # No operationId
        spec = make_api_spec(endpoints=[endpoint])
        analyzer = DefaultAnalyzer()
        result = analyzer.analyze(spec)
        assert isinstance(result, Ok)
        analyzed = result.value
        assert len(analyzed.warnings) > 0

    def test_resource_tree_built(self) -> None:
        spec = make_petstore_spec()
        analyzer = DefaultAnalyzer()
        result = analyzer.analyze(spec)
        assert isinstance(result, Ok)
        analyzed = result.value
        # Root should have children
        assert len(analyzed.resource_tree.children) > 0

    def test_nested_resource_detection(self) -> None:
        endpoints = [
            make_endpoint("/projects/{projId}/tasks", HttpMethod.GET, "listProjectTasks"),
            make_endpoint("/projects/{projId}/tasks/{taskId}", HttpMethod.GET, "getProjectTask"),
            make_endpoint("/projects", HttpMethod.GET, "listProjects"),
        ]
        spec = make_api_spec(endpoints=endpoints)
        analyzer = DefaultAnalyzer()
        result = analyzer.analyze(spec)
        assert isinstance(result, Ok)
        analyzed = result.value
        assert len(analyzed.resources) >= 2

    def test_analyzed_spec_json_round_trip(self) -> None:
        spec = make_petstore_spec()
        analyzer = DefaultAnalyzer()
        result = analyzer.analyze(spec)
        assert isinstance(result, Ok)
        analyzed = result.value
        json_str = analyzed.model_dump_json()
        from api2cli.models.analyzed import AnalyzedSpec
        restored = AnalyzedSpec.model_validate_json(json_str)
        assert len(restored.resources) == len(analyzed.resources)
