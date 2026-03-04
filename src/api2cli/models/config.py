from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from api2cli.models.commands import OutputFormat
from api2cli.models.spec import SpecFormat


class AuthConfig(BaseModel):
    """Authentication configuration."""

    type: str = "none"
    token: str | None = None
    key_name: str | None = None
    key_value: str | None = None
    username: str | None = None
    password: str | None = None
    in_: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


class Credential(BaseModel):
    """Stored credential for an API."""

    api_id: str
    auth_config: AuthConfig = Field(default_factory=AuthConfig)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    extensions: dict[str, Any] = Field(default_factory=dict)


class DefaultsConfig(BaseModel):
    """Default settings for the CLI."""

    output_format: OutputFormat = OutputFormat.JSON
    timeout: float = 30.0
    max_retries: int = 3
    base_url: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


class SpecConfig(BaseModel):
    """Spec source configuration."""

    path: str | None = None
    format: SpecFormat = SpecFormat.UNKNOWN
    base_url: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


class AppConfig(BaseModel):
    """Main application configuration."""

    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    spec: SpecConfig = Field(default_factory=SpecConfig)
    credentials_file: str | None = None
    config_version: str = "1"
    extensions: dict[str, Any] = Field(default_factory=dict)
