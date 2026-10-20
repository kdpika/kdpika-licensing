# Getting started

Use Python 3.11–3.14 and a private virtualenv. Install the published release
with `python -m pip install "kdpika-licensing==1.1.2"`. Check the
[PyPI release history](https://pypi.org/project/kdpika-licensing/#history)
for availability. For an unpublished source checkout, use
`python -m pip install .` instead.

Create a product and disposable Sandbox license in the platform. Configure
KDP_APP_ID, KDP_STATE_DIR, KDP_LICENSE_KEY and optional KDP_CUSTOMER_EMAIL
privately. The state directory must survive app restarts/upgrades.

Run `python examples/basic.py` from the source archive/checkout. It constructs
LicenseClient with environment="SANDBOX", checks current state and activates
only when NOT_ACTIVATED. See [Configuration](configuration.md) for every option.

~~~python
import os
from pathlib import Path
from kdpika_licensing import LicenseClient

client = LicenseClient(
    product=os.environ["KDP_APP_ID"],
    environment="SANDBOX",
    storage_dir=Path(os.environ["KDP_STATE_DIR"]),
)
result = client.check()
if result.error_code == "NOT_ACTIVATED":
    result = client.activate(os.environ["KDP_LICENSE_KEY"], os.getenv("KDP_CUSTOMER_EMAIL"))
if result.valid and result.signature_valid and result.feature("pdf_export"):
    print("Checked PDF export is permitted.")
~~~

Define pdf_export in your own plan if needed; it is not a built-in entitlement.
Never unlock work based on token presence, plain payload data or a failed result.
Before finishing a disposable test, run `python examples/session.py deactivate`
and verify success. Do not delete identity or state as a seat-release substitute.
