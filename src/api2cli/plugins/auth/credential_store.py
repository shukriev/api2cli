from __future__ import annotations

import json
import os
import stat
import warnings
from pathlib import Path

from platformdirs import user_config_dir

from api2cli.models.config import Credential


def _default_credentials_path() -> Path:
    """Return the default credentials file path."""
    return Path(user_config_dir("api2cli")) / "credentials.json"


class CredentialStore:
    """Persistent storage for API credentials.

    Credentials are stored as JSON at ~/.config/api2cli/credentials.json
    (or platform equivalent). File permissions are set to 0600 on Unix systems.

    Args:
        path: Custom path for the credentials file. Defaults to the
              platform-appropriate user config directory.
    """

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _default_credentials_path()

    def _load(self) -> dict[str, dict]:
        """Load credentials dict from disk."""
        if not self._path.exists():
            return {}
        try:
            raw = self._path.read_text(encoding="utf-8")
            return json.loads(raw)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self, data: dict[str, dict]) -> None:
        """Persist credentials dict to disk with secure permissions."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        if os.name == "posix":
            os.chmod(self._path, stat.S_IRUSR | stat.S_IWUSR)

    def _check_permissions(self) -> None:
        if os.name != "posix" or not self._path.exists():
            return
        file_stat = self._path.stat()
        mode = stat.S_IMODE(file_stat.st_mode)
        if mode & (stat.S_IRGRP | stat.S_IROTH | stat.S_IWGRP | stat.S_IWOTH):
            warnings.warn(
                f"Credentials file {self._path} has insecure permissions ({oct(mode)}). "
                "Run: chmod 600 " + str(self._path),
                stacklevel=2,
            )

    def get(self, ref: str) -> Credential | None:
        """Retrieve a credential by reference key.

        Args:
            ref: The credential reference key (e.g. API name or spec path).

        Returns:
            The stored Credential, or None if not found.
        """
        self._check_permissions()
        data = self._load()
        entry = data.get(ref)
        if entry is None:
            return None
        return Credential.model_validate(entry)

    def set(self, ref: str, credential: Credential) -> None:
        """Store a credential under the given reference key.

        Args:
            ref: The credential reference key.
            credential: The Credential to store.
        """
        data = self._load()
        data[ref] = json.loads(credential.model_dump_json())
        self._save(data)

    def delete(self, ref: str) -> bool:
        """Remove a credential by reference key.

        Args:
            ref: The credential reference key.

        Returns:
            True if the credential existed and was deleted, False otherwise.
        """
        data = self._load()
        if ref not in data:
            return False
        del data[ref]
        self._save(data)
        return True

    def list_refs(self) -> list[str]:
        """Return all stored credential reference keys."""
        return list(self._load().keys())
