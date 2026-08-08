import socket
from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.security.ssrf import (
    UnsafeTargetError,
    resolve_public_host,
    validate_public_ip,
    validate_resolved_addresses,
    validate_url_target,
)


def test_validate_public_ip_accepts_global_addresses() -> None:
    assert str(validate_public_ip("93.184.216.34")) == "93.184.216.34"
    assert (
        str(validate_public_ip("2606:2800:220:1:248:1893:25c8:1946"))
        == "2606:2800:220:1:248:1893:25c8:1946"
    )


def test_validate_public_ip_blocks_non_public_addresses() -> None:
    blocked_addresses = (
        "127.0.0.1",
        "10.0.0.1",
        "172.16.0.1",
        "192.168.1.1",
        "169.254.169.254",
        "0.0.0.0",
        "224.0.0.1",
        "::1",
        "fc00::1",
        "fe80::1",
    )

    for address in blocked_addresses:
        with pytest.raises(UnsafeTargetError):
            validate_public_ip(address)


def test_validate_resolved_addresses_rejects_empty_result() -> None:
    with pytest.raises(UnsafeTargetError):
        validate_resolved_addresses(())


@pytest.mark.anyio
async def test_resolve_public_host_accepts_public_addresses() -> None:
    event_loop = MagicMock()
    event_loop.getaddrinfo = AsyncMock(
        return_value=[
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("93.184.216.34", 443),
            ),
            (
                socket.AF_INET6,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                (
                    "2606:2800:220:1:248:1893:25c8:1946",
                    443,
                    0,
                    0,
                ),
            ),
        ],
    )

    with patch(
        "app.security.ssrf.asyncio.get_running_loop",
        return_value=event_loop,
    ):
        addresses = await resolve_public_host("example.com", 443)

    assert {str(address) for address in addresses} == {
        "93.184.216.34",
        "2606:2800:220:1:248:1893:25c8:1946",
    }


@pytest.mark.anyio
async def test_resolve_public_host_blocks_mixed_dns_result() -> None:
    event_loop = MagicMock()
    event_loop.getaddrinfo = AsyncMock(
        return_value=[
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("93.184.216.34", 443),
            ),
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("127.0.0.1", 443),
            ),
        ],
    )

    with (
        patch(
            "app.security.ssrf.asyncio.get_running_loop",
            return_value=event_loop,
        ),
        pytest.raises(UnsafeTargetError),
    ):
        await resolve_public_host("example.com", 443)


@pytest.mark.anyio
async def test_resolve_public_host_rejects_dns_failure() -> None:
    event_loop = MagicMock()
    event_loop.getaddrinfo = AsyncMock(
        side_effect=socket.gaierror,
    )

    with (
        patch(
            "app.security.ssrf.asyncio.get_running_loop",
            return_value=event_loop,
        ),
        pytest.raises(
            UnsafeTargetError,
            match="could not be resolved",
        ),
    ):
        await resolve_public_host("missing.example", 443)


@pytest.mark.anyio
async def test_validate_url_target_resolves_https_destination() -> None:
    addresses = (ip_address("93.184.216.34"),)

    with patch(
        "app.security.ssrf.resolve_public_host",
        new_callable=AsyncMock,
        return_value=addresses,
    ) as resolver:
        target = await validate_url_target(
            "https://example.com/health",
        )

    assert target.hostname == "example.com"
    assert target.port == 443
    assert target.addresses == addresses
    resolver.assert_awaited_once_with("example.com", 443)


@pytest.mark.anyio
async def test_validate_url_target_supports_explicit_http_port() -> None:
    with patch(
        "app.security.ssrf.resolve_public_host",
        new_callable=AsyncMock,
        return_value=(ip_address("93.184.216.34"),),
    ) as resolver:
        target = await validate_url_target(
            "http://example.com:8080/health",
        )

    assert target.port == 8080
    resolver.assert_awaited_once_with("example.com", 8080)


@pytest.mark.anyio
async def test_validate_url_target_rejects_unsafe_url_forms() -> None:
    unsafe_urls = (
        "ftp://example.com/file",
        "https://user:password@example.com",
        "https:///missing-host",
        "https://example.com:invalid",
    )

    for url in unsafe_urls:
        with pytest.raises(UnsafeTargetError):
            await validate_url_target(url)
