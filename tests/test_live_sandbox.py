"""Optional real Sandbox lifecycle. Not selected or connected by default.

Run only with an owner-provided disposable Sandbox key:
KDP_RUN_LIVE_SANDBOX=1 python -m pytest -m live tests/test_live_sandbox.py
KDP_APP_ID and KDP_LICENSE_KEY are required, KDP_CUSTOMER_EMAIL is optional.
No customer data is printed. The test always attempts to release its own seat.
"""

import os

import pytest

from kdpika_licensing import LicenseClient


@pytest.mark.live
@pytest.mark.skipif(os.getenv("KDP_RUN_LIVE_SANDBOX") != "1", reason="Sandbox opt-in required")
def test_explicit_sandbox_lifecycle(tmp_path):
    product = os.getenv("KDP_APP_ID")
    key = os.getenv("KDP_LICENSE_KEY")
    if not product or not key:
        pytest.skip("A disposable Sandbox App ID and key must be supplied privately")
    client = LicenseClient(
        product=product,
        environment="SANDBOX",
        base_url=os.getenv("KDP_BASE_URL", "https://licensing.kdpika.com"),
        storage_dir=tmp_path,
        prefer_keyring=False,
    )
    activated = False
    try:
        result = client.activate(key, os.getenv("KDP_CUSTOMER_EMAIL"))
        activated = result.valid and result.signature_valid
        assert activated, f"Sandbox activation refused: {result.error_code}"
        checked = client.check()
        assert checked.valid and checked.signature_valid
        refreshed = client.validate()
        assert refreshed.valid and refreshed.signature_valid and refreshed.source == "online"
    finally:
        if activated:
            released = client.deactivate()
            assert released.valid, f"Sandbox activation requires cleanup: {released.error_code}"
