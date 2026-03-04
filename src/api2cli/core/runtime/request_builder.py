from __future__ import annotations

import json
from typing import Any

from api2cli.models.commands import CommandNode
from api2cli.models.runtime import ApiRequest


class RequestBuilder:
    """Builds ApiRequest objects from command nodes and flag values."""

    def build(
        self,
        node: CommandNode,
        flag_values: dict[str, Any],
        base_url: str,
    ) -> ApiRequest:
        """Build an ApiRequest from a command node and flag values.

        Args:
            node: The command node with execution definition.
            flag_values: Parsed flag values from the CLI.
            base_url: The API base URL.

        Returns:
            ApiRequest ready for execution.

        Raises:
            ValueError: If the node has no execution definition.
        """
        if node.execution is None:
            raise ValueError(f"Command '{node.name}' has no execution definition")

        exec_def = node.execution

        url_path = exec_def.url_template
        for param_name in exec_def.path_params:
            flag_key = self._find_flag_value(param_name, flag_values)
            if flag_key is not None:
                url_path = url_path.replace(f"{{{param_name}}}", str(flag_key))

        url = base_url.rstrip("/") + url_path

        query_params: dict[str, Any] = {}
        for param_name in exec_def.query_params:
            flag_key = self._find_flag_value_key(param_name, flag_values)
            if flag_key and flag_key in flag_values:
                query_params[param_name] = flag_values[flag_key]

        headers: dict[str, str] = {
            "Content-Type": exec_def.content_type,
            "Accept": "application/json",
        }
        for param_name in exec_def.header_params:
            flag_key = self._find_flag_value_key(param_name, flag_values)
            if flag_key and flag_key in flag_values:
                headers[param_name] = str(flag_values[flag_key])

        body: Any = None
        if exec_def.body_param and exec_def.body_param in flag_values:
            body_value = flag_values[exec_def.body_param]
            if isinstance(body_value, str):
                try:
                    body = json.loads(body_value)
                except json.JSONDecodeError:
                    body = body_value
            else:
                body = body_value
        elif exec_def.body_fields:
            body_dict: dict[str, Any] = {}
            for field_name in exec_def.body_fields:
                flag_key_name = self._find_flag_value_key(field_name, flag_values)
                if flag_key_name and flag_key_name in flag_values:
                    body_dict[field_name] = flag_values[flag_key_name]
            if body_dict:
                body = body_dict
        else:
            body_dict = {}
            flag_map = {f.name: f for f in node.flags}
            for flag_name, flag_value in flag_values.items():
                flag_def = flag_map.get(flag_name)
                if (
                    flag_def
                    and flag_name not in exec_def.path_params
                    and flag_name not in exec_def.query_params
                    and flag_name not in exec_def.header_params
                    and exec_def.method in ("POST", "PUT", "PATCH")
                ):
                    body_dict[flag_name] = flag_value
            if body_dict and exec_def.method in ("POST", "PUT", "PATCH"):
                body = body_dict

        return ApiRequest(
            method=exec_def.method,
            url=url,
            headers=headers,
            params=query_params,
            body=body,
        )

    def _find_flag_value(self, param_name: str, flag_values: dict[str, Any]) -> Any:
        """Find a flag value by param name, trying different case variants.

        Args:
            param_name: The parameter name to look up.
            flag_values: Dictionary of flag values.

        Returns:
            The flag value, or None if not found.
        """
        key = self._find_flag_value_key(param_name, flag_values)
        return flag_values.get(key) if key else None

    def _find_flag_value_key(self, param_name: str, flag_values: dict[str, Any]) -> str | None:
        """Find the flag key for a param name.

        Args:
            param_name: The parameter name to look up.
            flag_values: Dictionary of flag values.

        Returns:
            The matching key in flag_values, or None if not found.
        """
        from api2cli.core.analyzer.naming_engine import to_kebab_case

        if param_name in flag_values:
            return param_name
        kebab = to_kebab_case(param_name)
        if kebab in flag_values:
            return kebab
        return None


def build_curl_command(request: ApiRequest) -> str:
    """Build a curl command string from an ApiRequest.

    Args:
        request: The API request to represent as curl.

    Returns:
        A curl command string.
    """
    parts = ["curl", "-X", request.method]

    for key, value in request.headers.items():
        parts.extend(["-H", f"'{key}: {value}'"])

    url = request.url
    if request.params:
        param_str = "&".join(f"{k}={v}" for k, v in request.params.items())
        url = f"{url}?{param_str}"

    if request.body is not None:
        body_str = json.dumps(request.body)
        parts.extend(["-d", f"'{body_str}'"])

    parts.append(f"'{url}'")
    return " ".join(parts)
