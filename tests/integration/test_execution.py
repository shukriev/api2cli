from __future__ import annotations

import json
from pathlib import Path

import httpx
import respx
from typer.testing import CliRunner

from api2cli.cli.main import app

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "openapi"
runner = CliRunner()


class TestDryRun:
    def test_dry_run_prints_curl(self) -> None:
        petstore = str(FIXTURES_DIR / "petstore.yaml")
        result = runner.invoke(
            app,
            ["run", "--spec", petstore, "--dry-run", "pets", "list"],
        )
        assert result.exit_code == 0
        assert "curl" in result.output.lower()

    def test_dry_run_get_with_param(self) -> None:
        petstore = str(FIXTURES_DIR / "petstore.yaml")
        result = runner.invoke(
            app,
            ["run", "--spec", petstore, "--dry-run", "pets", "get", "--pet-id", "123"],
        )
        assert result.exit_code == 0
        assert "curl" in result.output.lower()


class TestHttpExecution:
    def test_list_pets_json_output(self) -> None:
        with respx.mock(assert_all_called=False) as mock:
            mock.get("https://petstore.example.com/pets").mock(
                return_value=httpx.Response(
                    200,
                    json=[{"id": "1", "name": "Fluffy"}, {"id": "2", "name": "Spot"}],
                )
            )
            petstore = str(FIXTURES_DIR / "petstore.yaml")
            result = runner.invoke(
                app,
                ["run", "--spec", petstore, "--output", "json", "pets", "list"],
            )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 2

    def test_get_pet_json_output(self) -> None:
        with respx.mock(assert_all_called=False) as mock:
            mock.get("https://petstore.example.com/pets/42").mock(
                return_value=httpx.Response(
                    200,
                    json={"id": "42", "name": "Fluffy"},
                )
            )
            petstore = str(FIXTURES_DIR / "petstore.yaml")
            result = runner.invoke(
                app,
                ["run", "--spec", petstore, "pets", "get", "--pet-id", "42"],
            )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "42"

    def test_error_response_non_zero_exit(self) -> None:
        with respx.mock(assert_all_called=False) as mock:
            mock.get("https://petstore.example.com/pets/999").mock(
                return_value=httpx.Response(
                    404,
                    json={"message": "Pet not found"},
                )
            )
            petstore = str(FIXTURES_DIR / "petstore.yaml")
            result = runner.invoke(
                app,
                ["run", "--spec", petstore, "pets", "get", "--pet-id", "999"],
            )
        assert result.exit_code != 0

    def test_table_output_format(self) -> None:
        with respx.mock(assert_all_called=False) as mock:
            mock.get("https://petstore.example.com/pets").mock(
                return_value=httpx.Response(
                    200,
                    json=[{"id": "1", "name": "Fluffy"}],
                )
            )
            petstore = str(FIXTURES_DIR / "petstore.yaml")
            result = runner.invoke(
                app,
                ["run", "--spec", petstore, "--output", "table", "pets", "list"],
            )
        assert result.exit_code == 0
        # Table output should contain the data
        assert "Fluffy" in result.output or "id" in result.output.lower()
