"""Default suite cannot open a real connection. All signing keys are ephemeral."""

import os
import socket

import pytest
from test_security import session as session


@pytest.fixture(autouse=True)
def no_live_network(monkeypatch, request):
    if request.node.get_closest_marker("live") and os.getenv("KDP_RUN_LIVE_SANDBOX") == "1":
        return

    def reject(*args, **kwargs):
        raise AssertionError("Default tests must use a mock transport, not a live network")

    monkeypatch.setattr(socket.socket, "connect", reject)
    monkeypatch.setattr(socket.socket, "connect_ex", reject)
