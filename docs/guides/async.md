# Async and concurrency

~~~python
from kdpika_licensing import AsyncLicenseClient

async def permitted(sync_client):
    client = AsyncLicenseClient(sync_client)
    result = await client.check()
    return result.valid and result.signature_valid and result.feature("pdf_export")
~~~

Run examples/async_usage.py with private Sandbox KDP_* variables for the
complete lifecycle. The wrapper uses asyncio.to_thread, the same cryptographic
core and the same identity/state locks; it does not create an independent grant.

Cancellation of an await does not cancel a thread's in-flight request. Preserve
identity and reconcile an uncertain mutation before retrying. Ordinary POSTs
have no automatic retry. A local lock can time out after five seconds; slow
network work is intentionally serialized with state operations. Do not share
the directory across users or use NFS. Native Windows/Linux acceptance remains
separate from the locally executed macOS matrix.
