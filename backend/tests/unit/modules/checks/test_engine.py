from unittest.mock import AsyncMock, patch

import httpx2
import pytest

from app.modules.checks.engine import HttpCheckEngine
from app.modules.checks.results import CheckErrorType
from app.security.ssrf import UnsafeTargetError


@pytest.mark.anyio
async def test_execute_returns_successful_result() -> None:
    async def handler(_: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            content=b'{"status":"healthy"}',
        )

    transport = httpx2.MockTransport(handler)

    async with httpx2.AsyncClient(transport=transport) as client:
        engine = HttpCheckEngine(client)

        with patch(
            "app.modules.checks.engine.validate_url_target",
            new_callable=AsyncMock,
        ):
            result = await engine.execute(
                url="https://example.com/health",
                timeout_seconds=5,
                expected_status=200,
            )

    assert result.success is True
    assert result.status_code == 200
    assert result.body == b'{"status":"healthy"}'


@pytest.mark.anyio
async def test_execute_detects_unexpected_status() -> None:
    async def handler(_: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(503, content=b"unavailable")

    transport = httpx2.MockTransport(handler)

    async with httpx2.AsyncClient(transport=transport) as client:
        engine = HttpCheckEngine(client)

        with patch(
            "app.modules.checks.engine.validate_url_target",
            new_callable=AsyncMock,
        ):
            result = await engine.execute(
                url="https://example.com/health",
                timeout_seconds=5,
                expected_status=200,
            )

    assert result.success is False
    assert result.status_code == 503
    assert result.error_type is CheckErrorType.UNEXPECTED_STATUS


@pytest.mark.anyio
async def test_execute_limits_response_size() -> None:
    async def handler(_: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            content=b"response-is-too-large",
        )

    transport = httpx2.MockTransport(handler)

    async with httpx2.AsyncClient(transport=transport) as client:
        engine = HttpCheckEngine(
            client,
            max_response_bytes=10,
        )

        with patch(
            "app.modules.checks.engine.validate_url_target",
            new_callable=AsyncMock,
        ):
            result = await engine.execute(
                url="https://example.com/health",
                timeout_seconds=5,
                expected_status=200,
            )

    assert result.success is False
    assert result.error_type is CheckErrorType.RESPONSE_TOO_LARGE
    assert result.body == b""


@pytest.mark.anyio
async def test_execute_blocks_unsafe_target_before_request() -> None:
    async def handler(_: httpx2.Request) -> httpx2.Response:
        raise AssertionError("HTTP request must not be executed")

    transport = httpx2.MockTransport(handler)

    async with httpx2.AsyncClient(transport=transport) as client:
        engine = HttpCheckEngine(client)

        with patch(
            "app.modules.checks.engine.validate_url_target",
            new_callable=AsyncMock,
            side_effect=UnsafeTargetError,
        ):
            result = await engine.execute(
                url="http://127.0.0.1/health",
                timeout_seconds=5,
                expected_status=200,
            )

    assert result.success is False
    assert result.status_code is None
    assert result.error_type is CheckErrorType.UNSAFE_TARGET
    assert result.error_message == "Destination is not allowed"


@pytest.mark.anyio
async def test_execute_classifies_timeout() -> None:
    async def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ReadTimeout(
            "internal timeout details",
            request=request,
        )

    transport = httpx2.MockTransport(handler)

    async with httpx2.AsyncClient(transport=transport) as client:
        engine = HttpCheckEngine(client)

        with patch(
            "app.modules.checks.engine.validate_url_target",
            new_callable=AsyncMock,
        ):
            result = await engine.execute(
                url="https://example.com/health",
                timeout_seconds=5,
                expected_status=200,
            )

    assert result.success is False
    assert result.status_code is None
    assert result.error_type is CheckErrorType.TIMEOUT
    assert result.error_message == "Request timed out"


@pytest.mark.anyio
async def test_execute_classifies_connection_error() -> None:
    async def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError(
            "internal connection details",
            request=request,
        )

    transport = httpx2.MockTransport(handler)

    async with httpx2.AsyncClient(transport=transport) as client:
        engine = HttpCheckEngine(client)

        with patch(
            "app.modules.checks.engine.validate_url_target",
            new_callable=AsyncMock,
        ):
            result = await engine.execute(
                url="https://example.com/health",
                timeout_seconds=5,
                expected_status=200,
            )

    assert result.success is False
    assert result.status_code is None
    assert result.error_type is CheckErrorType.CONNECTION_ERROR
    assert result.error_message == "Request failed"


@pytest.mark.anyio
async def test_execute_validates_and_follows_redirect() -> None:
    async def handler(request: httpx2.Request) -> httpx2.Response:
        if request.url.path == "/start":
            return httpx2.Response(
                302,
                headers={"location": "/health"},
            )

        return httpx2.Response(200, content=b"healthy")

    transport = httpx2.MockTransport(handler)

    async with httpx2.AsyncClient(transport=transport) as client:
        engine = HttpCheckEngine(client)

        with patch(
            "app.modules.checks.engine.validate_url_target",
            new_callable=AsyncMock,
        ) as validator:
            result = await engine.execute(
                url="https://example.com/start",
                timeout_seconds=5,
                expected_status=200,
            )

    assert result.success is True
    assert result.body == b"healthy"
    assert validator.await_count == 2


@pytest.mark.anyio
async def test_execute_blocks_unsafe_redirect_destination() -> None:
    async def handler(_: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            302,
            headers={"location": "http://127.0.0.1/admin"},
        )

    transport = httpx2.MockTransport(handler)

    async with httpx2.AsyncClient(transport=transport) as client:
        engine = HttpCheckEngine(client)

        with patch(
            "app.modules.checks.engine.validate_url_target",
            new_callable=AsyncMock,
            side_effect=[None, UnsafeTargetError],
        ):
            result = await engine.execute(
                url="https://example.com/start",
                timeout_seconds=5,
                expected_status=200,
            )

    assert result.success is False
    assert result.error_type is CheckErrorType.UNSAFE_TARGET


@pytest.mark.anyio
async def test_execute_enforces_redirect_limit() -> None:
    async def handler(request: httpx2.Request) -> httpx2.Response:
        next_step = int(request.url.path.removeprefix("/step")) + 1

        return httpx2.Response(
            302,
            headers={"location": f"/step{next_step}"},
        )

    transport = httpx2.MockTransport(handler)

    async with httpx2.AsyncClient(transport=transport) as client:
        engine = HttpCheckEngine(
            client,
            max_redirects=1,
        )

        with patch(
            "app.modules.checks.engine.validate_url_target",
            new_callable=AsyncMock,
        ):
            result = await engine.execute(
                url="https://example.com/step1",
                timeout_seconds=5,
                expected_status=200,
            )

    assert result.success is False
    assert result.error_type is CheckErrorType.TOO_MANY_REDIRECTS
