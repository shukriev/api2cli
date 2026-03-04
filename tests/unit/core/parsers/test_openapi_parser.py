from __future__ import annotations

from pathlib import Path

from api2cli.core.parsers import parse_spec
from api2cli.core.parsers.openapi_parser import OpenApiParser
from api2cli.core.parsers.spec_input import SpecInput
from api2cli.errors import Err, Ok
from api2cli.models.spec import (
    HttpMethod,
    ParameterLocation,
    SecuritySchemeType,
    SpecFormat,
)

FIXTURES_DIR = Path(__file__).parent.parent.parent.parent / "fixtures" / "openapi"


class TestOpenApiParserCanParse:
    def test_detects_openapi_json(self) -> None:
        parser = OpenApiParser()
        content = '{"openapi": "3.0.3", "info": {"title": "T", "version": "1"}, "paths": {}}'
        assert parser.can_parse(content) is True

    def test_detects_openapi_yaml(self) -> None:
        parser = OpenApiParser()
        content = "openapi: '3.0.3'\ninfo:\n  title: T\n  version: '1'\npaths: {}"
        assert parser.can_parse(content) is True

    def test_rejects_non_openapi(self) -> None:
        parser = OpenApiParser()
        assert parser.can_parse("{}") is False
        assert parser.can_parse("random text") is False


class TestOpenApiParserMinimal:
    def test_parse_minimal_json(self) -> None:
        content = (FIXTURES_DIR / "minimal.json").read_text()
        parser = OpenApiParser()
        result = parser.parse(content, source="minimal.json")
        assert isinstance(result, Ok)
        spec = result.value
        assert spec.info.title == "Minimal API"
        assert spec.format == SpecFormat.OPENAPI
        assert len(spec.endpoints) == 1
        assert spec.endpoints[0].operation_id == "health"

    def test_parse_invalid_spec(self) -> None:
        content = (FIXTURES_DIR / "invalid_spec.yaml").read_text()
        parser = OpenApiParser()
        result = parser.parse(content, source="invalid_spec.yaml")
        assert isinstance(result, Err)

    def test_parse_malformed_yaml(self) -> None:
        parser = OpenApiParser()
        result = parser.parse(":\n  - :\n    invalid: [", source="bad.yaml")
        assert isinstance(result, Err)


class TestOpenApiParserPetstore:
    def setup_method(self) -> None:
        content = (FIXTURES_DIR / "petstore.yaml").read_text()
        parser = OpenApiParser()
        result = parser.parse(content, source="petstore.yaml")
        assert isinstance(result, Ok)
        self.spec = result.value

    def test_info_parsed(self) -> None:
        assert self.spec.info.title == "Petstore"
        assert self.spec.info.version == "1.0.0"

    def test_servers_parsed(self) -> None:
        assert len(self.spec.servers) >= 1
        assert "petstore.example.com" in self.spec.servers[0].url

    def test_endpoints_count(self) -> None:
        # petstore has: GET /pets, POST /pets, GET /pets/{id}, PUT /pets/{id},
        # DELETE /pets/{id}, GET /owners, GET /owners/{id}, DELETE /owners/{id}
        assert len(self.spec.endpoints) >= 7

    def test_tags_parsed(self) -> None:
        tag_names = [t.name for t in self.spec.tags]
        assert "pets" in tag_names
        assert "owners" in tag_names

    def test_security_schemes(self) -> None:
        assert "ApiKeyAuth" in self.spec.security_schemes
        assert "BearerAuth" in self.spec.security_schemes
        assert self.spec.security_schemes["ApiKeyAuth"].type == SecuritySchemeType.API_KEY
        assert self.spec.security_schemes["BearerAuth"].type == SecuritySchemeType.HTTP

    def test_list_endpoint(self) -> None:
        list_ep = next(
            ep for ep in self.spec.endpoints
            if ep.path == "/pets" and ep.method == HttpMethod.GET
        )
        assert list_ep.operation_id == "listPets"
        # Should have limit and offset params
        param_names = [p.name for p in list_ep.parameters]
        assert "limit" in param_names
        assert "offset" in param_names

    def test_path_param_merged(self) -> None:
        get_pet = next(
            ep for ep in self.spec.endpoints
            if ep.path == "/pets/{petId}" and ep.method == HttpMethod.GET
        )
        path_params = [p for p in get_pet.parameters if p.location == ParameterLocation.PATH]
        assert len(path_params) >= 1
        assert path_params[0].name == "petId"
        assert path_params[0].required is True


class TestOpenApiParserComplexParams:
    def setup_method(self) -> None:
        content = (FIXTURES_DIR / "complex_params.yaml").read_text()
        parser = OpenApiParser()
        result = parser.parse(content, source="complex_params.yaml")
        assert isinstance(result, Ok)
        self.spec = result.value

    def test_all_parameter_locations(self) -> None:
        list_ep = next(
            ep for ep in self.spec.endpoints
            if ep.method == HttpMethod.GET
        )
        locations = {p.location for p in list_ep.parameters}
        # Should have path (from path-level), query, header, cookie
        assert ParameterLocation.PATH in locations
        assert ParameterLocation.QUERY in locations
        assert ParameterLocation.HEADER in locations
        assert ParameterLocation.COOKIE in locations

    def test_path_level_param_merged(self) -> None:
        # resourceId is defined at path level, should be in all operations
        for ep in self.spec.endpoints:
            param_names = [p.name for p in ep.parameters]
            assert "resourceId" in param_names

    def test_oauth2_security_scheme(self) -> None:
        assert "OAuth2" in self.spec.security_schemes
        oauth = self.spec.security_schemes["OAuth2"]
        assert oauth.type == SecuritySchemeType.OAUTH2
        assert oauth.flows is not None
        assert oauth.flows.authorization_code is not None
        assert oauth.flows.authorization_code.token_url == "https://example.com/oauth/token"

    def test_request_body_parsed(self) -> None:
        post_ep = next(
            ep for ep in self.spec.endpoints
            if ep.method == HttpMethod.POST
        )
        assert post_ep.request_body is not None
        assert "application/json" in post_ep.request_body.content


class TestParseSpec:
    def test_parse_openapi_via_parse_spec(self) -> None:
        content = (FIXTURES_DIR / "minimal.json").read_text()
        spec_input = SpecInput.from_string(content, source="minimal.json")
        result = parse_spec(spec_input)
        assert isinstance(result, Ok)

    def test_parse_unknown_format(self) -> None:
        spec_input = SpecInput.from_string("this is not a spec")
        result = parse_spec(spec_input)
        assert isinstance(result, Err)

    def test_spec_input_from_file(self) -> None:
        path = FIXTURES_DIR / "minimal.json"
        spec_input = SpecInput.from_file(path)
        assert spec_input.source == str(path)
        assert '"openapi"' in spec_input.content
