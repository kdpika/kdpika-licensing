"""Run actual example quickstart/CLI/async against the fresh installed package."""

import importlib
import os
import socket
import sys
import tempfile
from pathlib import Path

from installed_smoke import Transport

from kdpika_licensing import LicenseClient

ROOT = Path(__file__).resolve().parents[1]


def main():
    def deny(*args, **kwargs):
        raise AssertionError("Installed example smoke must not use real network")

    socket.socket.connect = deny
    socket.socket.connect_ex = deny
    sys.path.insert(0, str(ROOT / "examples"))
    common = importlib.import_module("_common")
    transport = Transport()
    with tempfile.TemporaryDirectory(prefix="kdpika-installed-example-") as state:
        os.environ.update(
            {
                "KDP_APP_ID": "app_synthetic",
                "KDP_STATE_DIR": state,
                "KDP_LICENSE_KEY": "SYNTHETIC-NOT-A-REAL-KEY",
                "KDP_CUSTOMER_EMAIL": "tester@example.invalid",
            }
        )
        common.LicenseClient = lambda **kw: LicenseClient(**kw, transport=transport, prefer_keyring=False)
        assert importlib.import_module("basic").main() == 0
        session = importlib.import_module("session")
        assert session.main(["status"]) == 0
        assert session.main(["validate"]) == 0
        assert importlib.import_module("async_usage").main() == 0
        assert session.main(["deactivate"]) == 0
    print("PASS installed README-equivalent quickstart, CLI and async example paths; no live network")


if __name__ == "__main__":
    main()
