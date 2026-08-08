from time import perf_counter
from urllib.parse import urljoin

import httpx2

from app.modules.checks.results import (
    CheckErrorType,
    HttpCheckResult,
)
from app.security.ssrf import (
    UnsafeTargetError,
    validate_url_target,
)

DEFAULT_MAX_RESPONSE_BYTES = 1_000_000
DEFAULT_MAX_REDIRECTS = 3

_REDIRECT_STATUS_CODES = {
    301,
    302,
    303,
    307,
    308,
}


class ResponseTooLargeError(Exception):
    pass


class TooManyRedirectsError(Exception):
    pass


class HttpCheckEngine:
    def __init__(
        self,
        client: httpx2.AsyncClient,
        *,
        max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
        max_redirects: int = DEFAULT_MAX_REDIRECTS,
    ) -> None:
        self.client = client
        self.max_response_bytes = max_response_bytes
        self.max_redirects = max_redirects

    async def execute(
        self,
        *,
        url: str,
        timeout_seconds: int,
        expected_status: int,
    ) -> HttpCheckResult:
        started_at = perf_counter()
        current_url = url
        redirect_count = 0

        try:
            while True:
                await validate_url_target(current_url)

                async with self.client.stream(
                    "GET",
                    current_url,
                    timeout=timeout_seconds,
                    follow_redirects=False,
                ) as response:
                    location = response.headers.get("location")

                    if (
                        response.status_code in _REDIRECT_STATUS_CODES
                        and location is not None
                    ):
                        if redirect_count >= self.max_redirects:
                            raise TooManyRedirectsError

                        current_url = urljoin(current_url, location)
                        redirect_count += 1
                        continue

                    body = await self._read_limited_body(response)
                    status_code = response.status_code

                break

            response_time_ms = self._elapsed_milliseconds(started_at)

            if status_code != expected_status:
                return HttpCheckResult(
                    success=False,
                    status_code=status_code,
                    response_time_ms=response_time_ms,
                    error_type=CheckErrorType.UNEXPECTED_STATUS,
                    error_message=(
                        f"Expected HTTP {expected_status} but received {status_code}"
                    ),
                    body=body,
                )

            return HttpCheckResult(
                success=True,
                status_code=status_code,
                response_time_ms=response_time_ms,
                body=body,
            )
        except UnsafeTargetError:
            return self._error_result(
                started_at,
                CheckErrorType.UNSAFE_TARGET,
                "Destination is not allowed",
            )
        except TooManyRedirectsError:
            return self._error_result(
                started_at,
                CheckErrorType.TOO_MANY_REDIRECTS,
                "Response exceeded the redirect limit",
            )
        except ResponseTooLargeError:
            return self._error_result(
                started_at,
                CheckErrorType.RESPONSE_TOO_LARGE,
                "Response exceeded the allowed size",
            )
        except httpx2.TimeoutException:
            return self._error_result(
                started_at,
                CheckErrorType.TIMEOUT,
                "Request timed out",
            )
        except httpx2.RequestError:
            return self._error_result(
                started_at,
                CheckErrorType.CONNECTION_ERROR,
                "Request failed",
            )

    async def _read_limited_body(
        self,
        response: httpx2.Response,
    ) -> bytes:
        content_length = response.headers.get("content-length")

        if content_length is not None:
            try:
                declared_length = int(content_length)
            except ValueError:
                declared_length = 0

            if declared_length > self.max_response_bytes:
                raise ResponseTooLargeError

        body = bytearray()

        async for chunk in response.aiter_bytes():
            body.extend(chunk)

            if len(body) > self.max_response_bytes:
                raise ResponseTooLargeError

        return bytes(body)

    def _error_result(
        self,
        started_at: float,
        error_type: CheckErrorType,
        message: str,
    ) -> HttpCheckResult:
        return HttpCheckResult(
            success=False,
            status_code=None,
            response_time_ms=self._elapsed_milliseconds(started_at),
            error_type=error_type,
            error_message=message,
        )

    @staticmethod
    def _elapsed_milliseconds(started_at: float) -> int:
        return max(
            0,
            round((perf_counter() - started_at) * 1000),
        )
