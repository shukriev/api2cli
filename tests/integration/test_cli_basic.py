from __future__ import annotations

import json
from pathlib import Path

import httpx
import respx
from typer.testing import CliRunner

from api2cli.cli.main import app

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "openapi"


runner = CliRunner()


class TestVersionCommand:
    def test_version_output(self) -> None:
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "api2cli" in result.output
        assert "0.1.0" in result.output


class TestCapabilities:
    def test_capabilities_json_output(self) -> None:
        petstore = str(FIXTURES_DIR / "petstore.yaml")
        result = runner.invoke(app, ["run", "--spec", petstore, "--capabilities"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "commands" in data
        assert "api" in data
        assert data["api"]["title"] == "Petstore"

    def test_capabilities_has_pets_commands(self) -> None:
        petstore = str(FIXTURES_DIR / "petstore.yaml")
        result = runner.invoke(app, ["run", "--spec", petstore, "--capabilities"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "pets" in data["commands"]

    def test_capabilities_missing_spec(self) -> None:
        result = runner.invoke(app, ["run", "--capabilities"])
        assert result.exit_code != 0

    def test_capabilities_invalid_spec_path(self) -> None:
        result = runner.invoke(app, ["run", "--spec", "/nonexistent/spec.yaml", "--capabilities"])
        assert result.exit_code != 0


class TestSpecFromUrl:
    @respx.mock
    def test_capabilities_from_url(self) -> None:
        petstore_content = (FIXTURES_DIR / "petstore.yaml").read_text()
        respx.get("https://example.com/petstore.yaml").mock(
            return_value=httpx.Response(200, text=petstore_content)
        )
        result = runner.invoke(app, ["run", "--spec", "https://example.com/petstore.yaml", "--capabilities"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["api"]["title"] == "Petstore"
        assert "pets" in data["commands"]

    @respx.mock
    def test_url_spec_404_exits_nonzero(self) -> None:
        respx.get("https://example.com/missing.yaml").mock(
            return_value=httpx.Response(404)
        )
        result = runner.invoke(app, ["run", "--spec", "https://example.com/missing.yaml", "--capabilities"])
        assert result.exit_code != 0

    @respx.mock
    def test_url_spec_network_error_exits_nonzero(self) -> None:
        respx.get("https://example.com/spec.yaml").mock(
            side_effect=httpx.ConnectError("connection refused")
        )
        result = runner.invoke(app, ["run", "--spec", "https://example.com/spec.yaml", "--capabilities"])
        assert result.exit_code != 0


class TestDescribe:
    def test_describe_existing_command(self) -> None:
        petstore = str(FIXTURES_DIR / "petstore.yaml")
        result = runner.invoke(app, ["run", "--spec", petstore, "--describe", "pets.list"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "list"

    def test_describe_nonexistent_command(self) -> None:
        petstore = str(FIXTURES_DIR / "petstore.yaml")
        result = runner.invoke(app, ["run", "--spec", petstore, "--describe", "nonexistent.command"])
        assert result.exit_code != 0

    def test_describe_with_space_notation(self) -> None:
        petstore = str(FIXTURES_DIR / "petstore.yaml")
        result = runner.invoke(app, ["run", "--spec", petstore, "--describe", "pets list"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "list"
