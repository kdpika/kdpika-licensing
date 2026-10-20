"""Shared private configuration for the Sandbox examples; never print secrets."""

import getpass
import json
import os
from pathlib import Path

from kdpika_licensing import LicenseClient, LicenseResult, LicenseSdkError


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError("Missing required example configuration: " + name)
    return value


def configured_client() -> LicenseClient:
    return LicenseClient(
        product=required("KDP_APP_ID"),
        environment="SANDBOX",
        base_url=os.getenv("KDP_BASE_URL", "https://licensing.kdpika.com"),
        application_name="KDPika SDK example",
        application_version=os.getenv("KDP_APP_VERSION", ""),
        storage_dir=Path(required("KDP_STATE_DIR")),
    )


def activate(client: LicenseClient) -> LicenseResult:
    key = os.getenv("KDP_LICENSE_KEY") or getpass.getpass("Sandbox license key: ")
    return client.activate(key, os.getenv("KDP_CUSTOMER_EMAIL") or None)


def ensure_activation(client: LicenseClient) -> LicenseResult:
    result = client.check()
    return activate(client) if result.error_code == "NOT_ACTIVATED" else result


def summary(result: LicenseResult) -> dict[str, object]:
    # Intentionally exclude customer payload, key, activation token and identity.
    return {
        "valid": result.valid,
        "signature_valid": result.signature_valid,
        "source": result.source,
        "error_code": result.error_code,
        "request_id": result.request_id,
    }


def emit(result: LicenseResult) -> int:
    print(json.dumps(summary(result)))
    return 0 if result.valid else 1


def run(function) -> None:
    try:
        raise SystemExit(function())
    except (LicenseSdkError, ValueError):
        print("License operation unavailable. Check configuration, permissions or contact the publisher.")
        raise SystemExit(2) from None
