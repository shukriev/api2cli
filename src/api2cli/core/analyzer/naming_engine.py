from __future__ import annotations

import re

# Common path prefixes to strip
API_PREFIXES = {"/api/v1", "/api/v2", "/api/v3", "/api", "/v1", "/v2", "/v3", "/rest"}

# Reserved CLI flag names that should not be used
RESERVED_FLAG_NAMES = {
    "help", "version", "verbose", "output", "dry-run", "all",
    "page", "limit", "format", "config", "spec", "auth", "token",
    "api-key", "from-stdin", "describe", "capabilities",
}

# Short flags reserved for global flags
RESERVED_SHORT_FLAGS = {"h", "v", "o"}


def strip_api_prefix(path: str) -> str:
    """Strip common API path prefixes.

    Args:
        path: API path like /api/v1/pets

    Returns:
        Stripped path like /pets
    """
    # Sort by length descending so longest prefix matches first
    for prefix in sorted(API_PREFIXES, key=len, reverse=True):
        if path.startswith(prefix):
            remaining = path[len(prefix):]
            # Ensure the remaining path starts with / or is empty
            if not remaining or remaining.startswith("/"):
                return remaining or "/"
    return path


def to_kebab_case(name: str) -> str:
    """Convert any case style to kebab-case.

    Handles camelCase, PascalCase, snake_case, and space-separated.

    Args:
        name: Input name in any case style.

    Returns:
        kebab-case version of the name.
    """
    # Replace underscores and spaces with hyphens
    name = name.replace("_", "-").replace(" ", "-")
    # Insert hyphens before uppercase letters (camelCase/PascalCase)
    name = re.sub(r"([a-z\d])([A-Z])", r"\1-\2", name)
    # Lowercase and remove consecutive hyphens
    name = name.lower()
    name = re.sub(r"-+", "-", name)
    # Remove leading/trailing hyphens
    return name.strip("-")


def to_snake_case(name: str) -> str:
    """Convert any case style to snake_case.

    Args:
        name: Input name in any case style.

    Returns:
        snake_case version of the name.
    """
    return to_kebab_case(name).replace("-", "_")


def path_to_resource_name(path_segment: str) -> str:
    """Convert a URL path segment to a CLI resource name.

    Args:
        path_segment: A URL path segment like 'petOwners' or 'pet-owners'.

    Returns:
        kebab-case resource name like 'pet-owners'.
    """
    return to_kebab_case(path_segment)


def operation_id_to_path(operation_id: str) -> list[str]:
    """Parse an operationId into a resource path + verb.

    Examples:
        listProjectTasks -> ["projects", "tasks", "list"]
        getUser -> ["users", "get"]
        createPetOwner -> ["pet-owners", "create"]
        listPets -> ["pets", "list"]

    Args:
        operation_id: The operationId string from the spec.

    Returns:
        List of path segments ending with the verb.
    """
    # Common CRUD verbs to look for at the start
    crud_verbs = ["list", "get", "create", "update", "patch", "delete", "remove",
                  "add", "set", "fetch", "retrieve", "find", "search", "upload",
                  "download", "send", "generate", "trigger", "cancel", "approve",
                  "reject", "activate", "deactivate", "enable", "disable", "check",
                  "validate", "count", "exists", "has", "is", "archive", "restore",
                  "preview", "publish", "unpublish", "deploy", "undeploy", "start",
                  "stop", "restart", "pause", "resume", "sync", "clone", "move",
                  "copy", "transfer", "link", "unlink", "attach", "detach", "export",
                  "import", "convert", "complete", "submit", "post"]

    # Split on camelCase boundaries
    parts = re.findall(r"[A-Z][a-z]*|[a-z]+|\d+", operation_id)
    if not parts:
        return [to_kebab_case(operation_id)]

    # Find the verb (usually the first word)
    lower_parts = [p.lower() for p in parts]

    verb = None
    resource_parts: list[str] = []

    if lower_parts[0] in crud_verbs:
        verb = lower_parts[0]
        resource_parts = lower_parts[1:]
    else:
        # Fallback: use the whole thing as action
        verb = "action"
        resource_parts = lower_parts

    # Convert resource parts to kebab-case resource name(s)
    # Group consecutive single-word segments into resource names
    # e.g., ["project", "task"] -> ["projects", "tasks"]
    # Pluralize if it looks like a list operation
    result_segments: list[str] = []
    for part in resource_parts:
        if part:
            result_segments.append(to_kebab_case(part))

    if not result_segments:
        return [verb or "action"]

    return result_segments + [verb or "action"]


def get_short_flag(name: str, taken: set[str]) -> str | None:
    """Find an available short flag for the given name.

    Args:
        name: The flag name (may be kebab-case).
        taken: Set of already-assigned short flags.

    Returns:
        A single character short flag, or None if none available.
    """
    # Try the first letter of the last word
    words = name.replace("-", " ").replace("_", " ").split()
    candidates: list[str] = []

    if words:
        candidates.append(words[-1][0].lower())
    if len(words) >= 2:
        candidates.append(words[0][0].lower())

    # Also try first letter of the whole name
    candidates.append(name[0].lower() if name else "")

    for candidate in candidates:
        if candidate and candidate not in RESERVED_SHORT_FLAGS and candidate not in taken:
            return candidate

    return None
