import asyncio
import socket
from collections.abc import Iterable
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv6Address, ip_address
from urllib.parse import urlsplit

IPAddress = IPv4Address | IPv6Address


@dataclass(frozen=True, slots=True)
class ValidatedTarget:
    url: str
    hostname: str
    port: int
    addresses: tuple[IPAddress, ...]


class UnsafeTargetError(ValueError):
    pass


def validate_public_ip(value: str | IPAddress) -> IPAddress:
    address = ip_address(value)

    if (
        not address.is_global
        or address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    ):
        raise UnsafeTargetError(
            f"Destination address is not public: {address}",
        )

    return address


def validate_resolved_addresses(
    values: Iterable[str | IPAddress],
) -> tuple[IPAddress, ...]:
    addresses = tuple(validate_public_ip(value) for value in values)

    if not addresses:
        raise UnsafeTargetError("Destination did not resolve to an address")

    return addresses


async def resolve_public_host(
    hostname: str,
    port: int,
) -> tuple[IPAddress, ...]:
    event_loop = asyncio.get_running_loop()

    try:
        results = await event_loop.getaddrinfo(
            hostname,
            port,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
    except socket.gaierror as error:
        raise UnsafeTargetError(
            "Destination hostname could not be resolved",
        ) from error

    addresses = sorted(
        {result[4][0] for result in results},
    )

    return validate_resolved_addresses(addresses)


async def validate_url_target(url: str) -> ValidatedTarget:
    try:
        parsed_url = urlsplit(url)
        port = parsed_url.port
    except ValueError as error:
        raise UnsafeTargetError("Destination URL is invalid") from error

    if parsed_url.scheme not in {"http", "https"}:
        raise UnsafeTargetError("Destination scheme is not allowed")

    if parsed_url.hostname is None:
        raise UnsafeTargetError("Destination hostname is missing")

    if parsed_url.username is not None or parsed_url.password is not None:
        raise UnsafeTargetError("Destination credentials are not allowed")

    resolved_port = port or (443 if parsed_url.scheme == "https" else 80)
    addresses = await resolve_public_host(
        parsed_url.hostname,
        resolved_port,
    )

    return ValidatedTarget(
        url=url,
        hostname=parsed_url.hostname,
        port=resolved_port,
        addresses=addresses,
    )
