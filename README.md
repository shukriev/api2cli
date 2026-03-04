# api2cli

Convert any API specification into an AI-optimized CLI tool — instantly.

Point `api2cli` at an OpenAPI spec and get a fully-routed command-line interface with flags, help text, auth, pagination, and structured output. No code generation required.

## Features

- **Dynamic CLI from any OpenAPI 3.x spec** — load from a local file or remote URL, no boilerplate, no generation step
- **AI introspection** — `--capabilities` emits a machine-readable JSON command map
- **Auth system** — API key, Bearer token, and HTTP Basic; resolved from flags, env vars, or a local credential store
- **Multiple output formats** — JSON (default), table, NDJSON
- **Dry-run mode** — prints the equivalent `curl` command without executing
- **Describe any command** — get full flag/type/example metadata for any endpoint

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager

## Installation

```bash
git clone <repo>
cd api2cli
uv sync
```

Run in development mode:

```bash
uv run api2cli --help
```

## Quick Start

```bash
# List all commands available in a spec (local file)
uv run api2cli run --spec openapi.yaml --capabilities

# List all commands from a remote spec URL
uv run api2cli run --spec https://api.example.com/openapi.yaml --capabilities

# Call an endpoint
uv run api2cli run --spec openapi.yaml pets list

# Call with parameters
uv run api2cli run --spec openapi.yaml pets get --pet-id 42

# Create a resource
uv run api2cli run --spec openapi.yaml pets create --body '{"name":"Fido"}'

# Dry-run: print curl without executing
uv run api2cli run --spec openapi.yaml --dry-run pets list
```

## Spec Sources

`--spec` accepts a local file path or an HTTP/HTTPS URL:

```bash
# Local file (YAML or JSON)
api2cli run --spec ./openapi.yaml --capabilities
api2cli run --spec /absolute/path/openapi.json --capabilities

# Remote URL
api2cli run --spec https://api.example.com/openapi.yaml --capabilities
api2cli run --spec https://raw.githubusercontent.com/org/repo/main/openapi.yaml --capabilities
```

URL specs are fetched with a 30-second timeout and follow redirects automatically. Non-2xx responses and network errors produce a non-zero exit code with a descriptive error message.

## Command Reference

### `api2cli run`

Run commands against an API spec dynamically.

```
api2cli run [OPTIONS] [COMMAND] [ARGS]...

Options:
  --spec, -s TEXT        Path or URL to API spec file (OpenAPI YAML/JSON)
  --output, -o TEXT      Output format: json (default), table, ndjson
  --dry-run              Print curl command without executing
  --capabilities         Print JSON command map and exit
  --describe TEXT        Describe a command, e.g. "pets.list"
  --auth-token TEXT      Bearer token for authentication
  --api-key TEXT         API key for authentication
  --basic-auth TEXT      Basic auth credentials (username:password)
```

#### Introspection

```bash
# Full command tree as JSON (useful for AI agents)
api2cli run --spec openapi.yaml --capabilities

# Describe a specific command with its flags
api2cli run --spec openapi.yaml --describe pets.list
api2cli run --spec openapi.yaml --describe "pets list"
```

#### Output formats

```bash
api2cli run --spec openapi.yaml -o json  pets list   # default
api2cli run --spec openapi.yaml -o table pets list
api2cli run --spec openapi.yaml -o ndjson pets list
```

### `api2cli auth`

Manage stored API credentials.

```
api2cli auth set    --spec <id> --type <bearer|apikey|basic> --value <value>
api2cli auth status --spec <id>
api2cli auth clear  --spec <id>
api2cli auth list
```

#### Examples

```bash
# Store a bearer token
api2cli auth set --spec my-api --type bearer --value eyJhbGci...

# Store an API key
api2cli auth set --spec my-api --type apikey --value sk-live-abc123

# Store basic auth
api2cli auth set --spec my-api --type basic --value admin:secret

# Check stored credentials
api2cli auth status --spec my-api

# Remove credentials
api2cli auth clear --spec my-api
```

Credentials are stored at `~/.config/api2cli/credentials.json` with `0600` permissions.

### `api2cli version`

Print the installed version.

```bash
api2cli version
```

## Authentication

Auth credentials are resolved in this priority order:

| Priority | Source |
|----------|--------|
| 1 | CLI flag (`--auth-token`, `--api-key`, `--basic-auth`) |
| 2 | Environment variable (`API2CLI_TOKEN`, `API2CLI_API_KEY`, `API2CLI_BASIC_AUTH`) |
| 3 | Credential store (`api2cli auth set`) |

```bash
# Via flag
api2cli run --spec openapi.yaml --auth-token mytoken users list

# Via environment variable
API2CLI_TOKEN=mytoken api2cli run --spec openapi.yaml users list

# Via stored credential
api2cli auth set --spec openapi.yaml --type bearer --value mytoken
api2cli run --spec openapi.yaml users list
```

## AI / MCP Usage

`api2cli` is designed to be consumed by AI agents. The `--capabilities` output is a structured JSON command map describing every endpoint, its flags, types, and examples:

```bash
api2cli run --spec openapi.yaml --capabilities
```

```json
{
  "api": { "title": "Petstore", "version": "1.0.0", "base_urls": ["https://petstore.example.com"] },
  "global_flags": [...],
  "commands": {
    "pets": {
      "name": "pets",
      "is_group": true,
      "children": {
        "list": {
          "name": "list",
          "description": "List pets",
          "flags": [
            { "name": "limit", "type": "integer", "required": false, "default": 100 },
            { "name": "status", "type": "string", "required": false, "choices": ["available","pending","sold"] }
          ],
          "execution": { "method": "GET", "url_template": "/pets" }
        },
        "get": { ... },
        "create": { ... }
      }
    }
  }
}
```

Use `--describe` to get the full schema for a single command:

```bash
api2cli run --spec openapi.yaml --describe pets.list
```

## Development

```bash
# Install dependencies (including dev extras)
uv sync --all-extras

# Run all tests
uv run pytest

# Unit tests only
uv run pytest tests/unit

# Integration tests only
uv run pytest tests/integration

# Test coverage
uv run pytest --cov=api2cli

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run mypy src/
```

## Project Structure

```
src/api2cli/
├── cli/            # Typer CLI entry points (main, run, auth)
├── core/
│   ├── parsers/    # OpenAPI / GraphQL / HAR spec parsers
│   ├── analyzer/   # Resource detection and CRUD classification
│   ├── generator/  # Command tree builder
│   └── runtime/    # HTTP execution, request building, response transform
├── plugins/
│   ├── auth/       # Auth providers + credential store
│   └── output/     # Output formatters (JSON, table)
├── models/         # Pydantic data models (spec, commands, runtime, config)
└── errors.py       # Result[T] pattern and exception hierarchy
```

## Supported Spec Formats

| Format | Status |
|--------|--------|
| OpenAPI 3.0 / 3.1 (JSON or YAML) | Supported |
| GraphQL SDL | Planned |
| HAR | Planned |

## License

MIT
