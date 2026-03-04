from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Ok[T]:
    """Successful result containing a value."""

    value: T

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self.value


@dataclass(frozen=True)
class Err[T]:
    """Failed result containing an error."""

    error: ApiCliError

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def unwrap(self) -> T:
        raise self.error


type Result[T] = Ok[T] | Err[T]


class ApiCliError(Exception):
    """Base exception for all api2cli errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ParseError(ApiCliError):
    """Raised when spec parsing fails."""


class AnalysisError(ApiCliError):
    """Raised when spec analysis fails."""


class GenerationError(ApiCliError):
    """Raised when command tree generation fails."""


class ExecutionError(ApiCliError):
    """Raised when HTTP execution fails."""


class AuthError(ApiCliError):
    """Raised when authentication fails."""


class ConfigError(ApiCliError):
    """Raised when configuration is invalid."""


class ValidationError(ApiCliError):
    """Raised when input validation fails."""
