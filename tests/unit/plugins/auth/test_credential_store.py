from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from api2cli.models.config import AuthConfig, Credential
from api2cli.plugins.auth.credential_store import CredentialStore


def _make_bearer_credential(api_id: str = "test-api") -> Credential:
    return Credential(
        api_id=api_id,
        auth_config=AuthConfig(type="bearer", token="tok123"),
    )


class TestCredentialStore:
    def test_get_returns_none_when_missing(self, tmp_path: Path) -> None:
        store = CredentialStore(path=tmp_path / "creds.json")
        assert store.get("nonexistent") is None

    def test_set_and_get_credential(self, tmp_path: Path) -> None:
        store = CredentialStore(path=tmp_path / "creds.json")
        cred = _make_bearer_credential("myapi")
        store.set("myapi", cred)
        retrieved = store.get("myapi")
        assert retrieved is not None
        assert retrieved.api_id == "myapi"
        assert retrieved.auth_config.token == "tok123"

    def test_set_creates_parent_dirs(self, tmp_path: Path) -> None:
        nested_path = tmp_path / "nested" / "deep" / "creds.json"
        store = CredentialStore(path=nested_path)
        store.set("api", _make_bearer_credential())
        assert nested_path.exists()

    def test_set_file_permissions_unix(self, tmp_path: Path) -> None:
        if os.name != "posix":
            pytest.skip("Unix-only test")
        store = CredentialStore(path=tmp_path / "creds.json")
        store.set("api", _make_bearer_credential())
        mode = stat.S_IMODE((tmp_path / "creds.json").stat().st_mode)
        assert mode == 0o600

    def test_delete_existing_credential(self, tmp_path: Path) -> None:
        store = CredentialStore(path=tmp_path / "creds.json")
        store.set("api", _make_bearer_credential())
        result = store.delete("api")
        assert result is True
        assert store.get("api") is None

    def test_delete_nonexistent_returns_false(self, tmp_path: Path) -> None:
        store = CredentialStore(path=tmp_path / "creds.json")
        assert store.delete("ghost") is False

    def test_list_refs_empty(self, tmp_path: Path) -> None:
        store = CredentialStore(path=tmp_path / "creds.json")
        assert store.list_refs() == []

    def test_list_refs_with_entries(self, tmp_path: Path) -> None:
        store = CredentialStore(path=tmp_path / "creds.json")
        store.set("api1", _make_bearer_credential("api1"))
        store.set("api2", _make_bearer_credential("api2"))
        refs = store.list_refs()
        assert sorted(refs) == ["api1", "api2"]

    def test_overwrite_existing_credential(self, tmp_path: Path) -> None:
        store = CredentialStore(path=tmp_path / "creds.json")
        store.set("api", _make_bearer_credential())
        updated = Credential(
            api_id="api",
            auth_config=AuthConfig(type="bearer", token="new-token"),
        )
        store.set("api", updated)
        retrieved = store.get("api")
        assert retrieved is not None
        assert retrieved.auth_config.token == "new-token"

    def test_missing_file_handled_gracefully(self, tmp_path: Path) -> None:
        path = tmp_path / "nonexistent.json"
        store = CredentialStore(path=path)
        assert store.list_refs() == []
        assert store.get("any") is None
