"""Explicitly opted-in Sandbox acceptance. Reads credentials from JSON on stdin."""

import json
import os
import sys
import tempfile
from pathlib import Path

from license_sdk import LicenseClient, NetworkError
from license_sdk.transport import HttpTransport


class OfflineTransport:
    def request(self, *args, **kwargs):
        raise NetworkError("Simulated connection failure.")


def require(result, source):
    if not result.valid or result.source != source or not result.signature_valid:
        raise RuntimeError(
            f"Expected a valid {source} decision; code={result.error_code}; request_id={result.request_id}"
        )


def main():
    if os.getenv("KDP_RUN_LIVE_SANDBOX") != "1":
        raise RuntimeError("Set KDP_RUN_LIVE_SANDBOX=1 to opt into Sandbox acceptance.")
    config = json.loads(sys.stdin.readline())
    if str(config.get("environment", "SANDBOX")).strip().upper() not in {"SANDBOX", "TEST"}:
        raise RuntimeError("Live acceptance permits the Sandbox environment only.")
    with tempfile.TemporaryDirectory(prefix="lmp-phase04-") as directory:
        client = LicenseClient(
            product=config["product"],
            environment=config.get("environment", "sandbox"),
            base_url=config["base_url"],
            application_name="PHASE 04 Live Acceptance",
            application_version="1.0.0",
            storage_dir=Path(directory),
            prefer_keyring=False,
        )
        activated = False
        try:
            result = client.activate(config["license_key"], config.get("email"))
            require(result, "online")
            activated = True
            require(client.check(), "cache")
            client.transport = OfflineTransport()
            require(client.validate(), "offline")
        finally:
            if activated:
                client.transport = HttpTransport(config["base_url"])
                deactivated = client.deactivate()
                if not deactivated.valid:
                    raise RuntimeError(
                        f"Live test could not release its activation: {deactivated.error_code}"
                    )
        print(
            json.dumps({"success": True, "online": True, "cache": True, "offline": True, "deactivated": True})
        )


if __name__ == "__main__":
    main()
