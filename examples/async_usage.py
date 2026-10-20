"""Run: python examples/async_usage.py. Cancellation does not undo HTTP operations."""

import asyncio
import os

from _common import configured_client, required, run, summary

from kdpika_licensing import AsyncLicenseClient


async def example() -> int:
    import json

    client = AsyncLicenseClient(configured_client())
    result = await client.check()
    if result.error_code == "NOT_ACTIVATED":
        result = await client.activate(required("KDP_LICENSE_KEY"), os.getenv("KDP_CUSTOMER_EMAIL"))
    print(json.dumps(summary(result)))
    return 0 if result.valid and result.signature_valid else 1


def main() -> int:
    return asyncio.run(example())


if __name__ == "__main__":
    run(main)
