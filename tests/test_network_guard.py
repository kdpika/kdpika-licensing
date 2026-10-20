"""Keep the test network guard strict without breaking Windows asyncio pipes."""

import asyncio
import socket

import pytest


@pytest.mark.parametrize("method", ["connect", "connect_ex"])
@pytest.mark.parametrize("host", ["127.0.0.1", "192.0.2.1"])
def test_ordinary_connections_are_blocked(method, host):
    with socket.socket() as connection:
        with pytest.raises(AssertionError, match="mock transport"):
            getattr(connection, method)((host, 443))


def test_socketpair_and_asyncio_remain_available():
    left, right = socket.socketpair()
    with left, right:
        left.sendall(b"wake")
        assert right.recv(4) == b"wake"

    async def wake():
        await asyncio.sleep(0)
        return True

    assert asyncio.run(wake())
