from __future__ import annotations

import pytest

from api2cli.errors import ApiCliError, Err, Ok, ParseError
from api2cli.models.analyzed import (
    AnalyzedSpec,
    CrudOperation,
    OperationDef,
    ResourceDef,
)
from api2cli.models.commands import (
    CommandNode,
    CommandTree,
    ExecutionDef,
    FlagDef,
    FlagType,
    OutputFormat,
    TreeMeta,
)
from api2cli.models.config import AppConfig, AuthConfig, DefaultsConfig, SpecConfig
from api2cli.models.runtime import (
    ApiRequest,
    OutputEnvelope,
    OutputError,
    PaginationInfo,
)
from api2cli.models.spec import (
    ApiInfo,
    ApiSpec,
    EndpointDef,
    HttpMethod,
    ParameterDef,
    ParameterLocation,
    SchemaDef,
    SecuritySchemeDef,
    SecuritySchemeType,
    ServerDef,
    SpecFormat,
)
from tests.factories.spec_factory import make_api_spec, make_endpoint, make_petstore_spec


class TestResultPattern:
    """Test the Result[T] pattern."""

    def test_ok_is_ok(self) -> None:
        """Ok.is_ok() returns True."""
        result: Ok[int] = Ok(value=42)
        assert result.is_ok()
        assert not result.is_err()

    def test_ok_unwrap(self) -> None:
        """Ok.unwrap() returns the contained value."""
        result: Ok[str] = Ok(value="hello")
        assert result.unwrap() == "hello"

    def test_err_is_err(self) -> None:
        """Err.is_err() returns True."""
        err = ParseError("parse failed")
        result: Err[int] = Err(error=err)
        assert result.is_err()
        assert not result.is_ok()

    def test_err_unwrap_raises(self) -> None:
        """Err.unwrap() raises the contained error."""
        err = ParseError("parse failed")
        result: Err[int] = Err(error=err)
        with pytest.raises(ParseError):
            result.unwrap()

    def test_api_cli_error_hierarchy(self) -> None:
        """ParseError is a subclass of ApiCliError."""
        err = ParseError("test", details={"key": "val"})
        assert isinstance(err, ApiCliError)
        assert err.message == "test"
        assert err.details == {"key": "val"}


class TestSpecModels:
    """Test spec models instantiation and JSON round-trip."""

    def test_api_info_round_trip(self) -> None:
        """ApiInfo can be serialized and deserialized."""
        info = ApiInfo(title="Test API", version="1.0.0", description="A test API")
        json_str = info.model_dump_json()
        restored = ApiInfo.model_validate_json(json_str)
        assert restored.title == info.title
        assert restored.version == info.version

    def test_schema_def_nested(self) -> None:
        """SchemaDef supports nested properties."""
        schema = SchemaDef(
            type="object",
            properties={
                "id": SchemaDef(type="integer"),
                "name": SchemaDef(type="string"),
            },
            required=["id"],
        )
        json_str = schema.model_dump_json()
        restored = SchemaDef.model_validate_json(json_str)
        assert "id" in restored.properties
        assert restored.properties["id"].type == "integer"

    def test_parameter_def_round_trip(self) -> None:
        """ParameterDef can be serialized and deserialized."""
        param = ParameterDef(
            name="petId",
            location=ParameterLocation.PATH,
            required=True,
            schema_def=SchemaDef(type="string"),
        )
        json_str = param.model_dump_json()
        restored = ParameterDef.model_validate_json(json_str)
        assert restored.name == "petId"
        assert restored.location == ParameterLocation.PATH
        assert restored.required is True

    def test_endpoint_def_round_trip(self) -> None:
        """EndpointDef can be serialized and deserialized."""
        endpoint = EndpointDef(
            path="/pets/{petId}",
            method=HttpMethod.GET,
            operation_id="getPet",
            tags=["pets"],
        )
        json_str = endpoint.model_dump_json()
        restored = EndpointDef.model_validate_json(json_str)
        assert restored.path == "/pets/{petId}"
        assert restored.method == HttpMethod.GET

    def test_api_spec_round_trip(self) -> None:
        """ApiSpec can be serialized and deserialized."""
        spec = make_api_spec()
        json_str = spec.model_dump_json()
        restored = ApiSpec.model_validate_json(json_str)
        assert restored.info.title == spec.info.title

    def test_petstore_spec(self) -> None:
        """Petstore factory produces the expected endpoint count."""
        spec = make_petstore_spec()
        assert len(spec.endpoints) == 7
        assert spec.info.title == "Petstore API"

    def test_security_scheme_def_round_trip(self) -> None:
        """SecuritySchemeDef can be serialized and deserialized."""
        scheme = SecuritySchemeDef(
            name_key="api_key",
            type=SecuritySchemeType.API_KEY,
            name="X-API-Key",
            in_=ParameterLocation.HEADER,
        )
        json_str = scheme.model_dump_json()
        restored = SecuritySchemeDef.model_validate_json(json_str)
        assert restored.type == SecuritySchemeType.API_KEY
        assert restored.name == "X-API-Key"

    def test_server_def_round_trip(self) -> None:
        """ServerDef can be serialized and deserialized."""
        server = ServerDef(url="https://api.example.com", description="Production")
        json_str = server.model_dump_json()
        restored = ServerDef.model_validate_json(json_str)
        assert restored.url == "https://api.example.com"

    @pytest.mark.parametrize("fmt", list(SpecFormat))
    def test_spec_format_enum(self, fmt: SpecFormat) -> None:
        """SpecFormat enum values are strings."""
        assert isinstance(fmt.value, str)

    @pytest.mark.parametrize("method", list(HttpMethod))
    def test_http_method_enum(self, method: HttpMethod) -> None:
        """HttpMethod enum values are strings."""
        assert isinstance(method.value, str)


class TestAnalyzedModels:
    """Test analyzed models."""

    def test_operation_def_round_trip(self) -> None:
        """OperationDef can be serialized and deserialized."""
        endpoint = make_endpoint()
        op = OperationDef(
            endpoint=endpoint,
            crud_operation=CrudOperation.LIST,
            resource_path=["pets"],
            cli_name="list",
            resource_name="pets",
        )
        json_str = op.model_dump_json()
        restored = OperationDef.model_validate_json(json_str)
        assert restored.crud_operation == CrudOperation.LIST
        assert restored.resource_path == ["pets"]

    def test_resource_def_round_trip(self) -> None:
        """ResourceDef can be serialized and deserialized."""
        resource = ResourceDef(
            name="pets",
            path_prefix="/pets",
        )
        json_str = resource.model_dump_json()
        restored = ResourceDef.model_validate_json(json_str)
        assert restored.name == "pets"

    def test_analyzed_spec_round_trip(self) -> None:
        """AnalyzedSpec can be serialized and deserialized."""
        spec = make_api_spec()
        analyzed = AnalyzedSpec(original_spec=spec)
        json_str = analyzed.model_dump_json()
        restored = AnalyzedSpec.model_validate_json(json_str)
        assert restored.original_spec.info.title == spec.info.title


class TestCommandModels:
    """Test command models."""

    def test_flag_def_round_trip(self) -> None:
        """FlagDef can be serialized and deserialized."""
        flag = FlagDef(
            name="limit",
            short="l",
            type=FlagType.INTEGER,
            default=10,
            description="Max items to return",
        )
        json_str = flag.model_dump_json()
        restored = FlagDef.model_validate_json(json_str)
        assert restored.name == "limit"
        assert restored.type == FlagType.INTEGER

    def test_execution_def_round_trip(self) -> None:
        """ExecutionDef can be serialized and deserialized."""
        exec_def = ExecutionDef(
            method="GET",
            url_template="/pets/{petId}",
            path_params=["petId"],
            query_params=["limit"],
        )
        json_str = exec_def.model_dump_json()
        restored = ExecutionDef.model_validate_json(json_str)
        assert restored.method == "GET"
        assert "petId" in restored.path_params

    def test_command_node_round_trip(self) -> None:
        """CommandNode can be serialized and deserialized."""
        node = CommandNode(
            name="list",
            path=["pets", "list"],
            description="List all pets",
            flags=[FlagDef(name="limit", type=FlagType.INTEGER)],
            is_group=False,
        )
        json_str = node.model_dump_json()
        restored = CommandNode.model_validate_json(json_str)
        assert restored.name == "list"
        assert len(restored.flags) == 1

    def test_command_tree_round_trip(self) -> None:
        """CommandTree can be serialized and deserialized."""
        tree = CommandTree(
            meta=TreeMeta(api_title="Test API", base_urls=["https://api.example.com"]),
            root=CommandNode(name="root", is_group=True),
        )
        json_str = tree.model_dump_json()
        restored = CommandTree.model_validate_json(json_str)
        assert restored.meta.api_title == "Test API"

    @pytest.mark.parametrize("fmt", list(OutputFormat))
    def test_output_format_enum(self, fmt: OutputFormat) -> None:
        """OutputFormat enum values are strings."""
        assert isinstance(fmt.value, str)


class TestRuntimeModels:
    """Test runtime models."""

    def test_output_envelope_round_trip(self) -> None:
        """OutputEnvelope can be serialized and deserialized."""
        envelope = OutputEnvelope(data={"id": 1, "name": "Fluffy"})
        json_str = envelope.model_dump_json()
        restored = OutputEnvelope.model_validate_json(json_str)
        assert restored.data == {"id": 1, "name": "Fluffy"}

    def test_api_request_round_trip(self) -> None:
        """ApiRequest can be serialized and deserialized."""
        request = ApiRequest(
            method="GET",
            url="https://api.example.com/pets",
            headers={"Authorization": "Bearer token"},
            params={"limit": 10},
        )
        json_str = request.model_dump_json()
        restored = ApiRequest.model_validate_json(json_str)
        assert restored.method == "GET"
        assert restored.headers["Authorization"] == "Bearer token"

    def test_output_error_round_trip(self) -> None:
        """OutputError can be serialized and deserialized."""
        error = OutputError(code="NOT_FOUND", message="Resource not found", http_status=404)
        json_str = error.model_dump_json()
        restored = OutputError.model_validate_json(json_str)
        assert restored.code == "NOT_FOUND"
        assert restored.http_status == 404

    def test_pagination_info_round_trip(self) -> None:
        """PaginationInfo can be serialized and deserialized."""
        info = PaginationInfo(page=1, total_pages=10, has_more=True, total_items=100)
        json_str = info.model_dump_json()
        restored = PaginationInfo.model_validate_json(json_str)
        assert restored.page == 1
        assert restored.has_more is True


class TestConfigModels:
    """Test config models."""

    def test_auth_config_round_trip(self) -> None:
        """AuthConfig can be serialized and deserialized."""
        auth = AuthConfig(type="bearer", token="my-secret-token")
        json_str = auth.model_dump_json()
        restored = AuthConfig.model_validate_json(json_str)
        assert restored.type == "bearer"
        assert restored.token == "my-secret-token"

    def test_app_config_defaults(self) -> None:
        """AppConfig has the expected defaults."""
        config = AppConfig()
        assert config.config_version == "1"
        assert config.defaults.timeout == 30.0

    def test_app_config_round_trip(self) -> None:
        """AppConfig can be serialized and deserialized."""
        config = AppConfig(
            defaults=DefaultsConfig(timeout=60.0),
            spec=SpecConfig(path="/path/to/spec.yaml"),
        )
        json_str = config.model_dump_json()
        restored = AppConfig.model_validate_json(json_str)
        assert restored.defaults.timeout == 60.0
        assert restored.spec.path == "/path/to/spec.yaml"
