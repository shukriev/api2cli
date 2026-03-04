from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

import httpx

from api2cli.errors import Err, ExecutionError, Ok
from api2cli.models.runtime import ApiRequest, ApiResponse, RequestTiming

type Result[T] = Ok[T] | Err[T]


class HttpxExecutor:
    """Async HTTP executor using httpx."""

    def __init__(
        self,
        timeout: float = 30.0,
        follow_redirects: bool = True,
    ) -> None:
        """Initialize the executor.

        Args:
            timeout: Default request timeout in seconds.
            follow_redirects: Whether to follow HTTP redirects.
        """
        self._timeout = timeout
        self._follow_redirects = follow_redirects

    async def execute(self, request: ApiRequest) -> Result[ApiResponse]:
        """Execute an HTTP request asynchronously.

        Args:
            request: The API request to execute.

        Returns:
            Ok(ApiResponse) on success, Err(ExecutionError) on failure.
        """
        start_time = datetime.utcnow()
        try:
            async with httpx.AsyncClient(
                timeout=request.timeout or self._timeout,
                follow_redirects=self._follow_redirects,
            ) as client:
                response = await client.request(
                    method=request.method,
                    url=request.url,
                    headers=request.headers,
                    params=request.params,
                    json=request.body if request.body is not None else None,
                )
            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            timing = RequestTiming(
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
            )

            body: Any = None
            content_type = response.headers.get("content-type", "")
            if "json" in content_type:
                try:
                    body = response.json()
                except Exception:
                    body = response.text
            else:
                body = response.text

            api_response = ApiResponse(
                status_code=response.status_code,
                headers=dict(response.headers),
                body=body,
                timing=timing,
            )
            return Ok(api_response)

        except httpx.TimeoutException as exc:
            return Err(ExecutionError(f"Request timed out: {exc}"))
        except httpx.NetworkError as exc:
            return Err(ExecutionError(f"Network error: {exc}"))
        except Exception as exc:
            return Err(ExecutionError(f"Request failed: {exc}"))

    def execute_sync(self, request: ApiRequest) -> Result[ApiResponse]:
        """Synchronous wrapper for execute().

        Args:
            request: The API request to execute.

        Returns:
            Ok(ApiResponse) on success, Err(ExecutionError) on failure.
        """
        return asyncio.run(self.execute(request))
