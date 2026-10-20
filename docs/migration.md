# Migration from studio-soline-license-sdk / license_sdk

1. Preserve private state and configuration; do not delete installation identity.
2. Stop processes using the old package. Remove the old distribution before
   installing the candidate so two distributions do not own license_sdk.
3. Install this checkout (or the approved version once published).
4. Replace license_sdk imports with kdpika_licensing.
5. Require valid AND signature_valid, then feature helpers before protected work.
6. Run the Sandbox lifecycle and restart/offline tests on your target platform.

Old imports/submodules remain warning shims. local/credentials/mutable transport
are deprecated internal escape hatches. State namespace/filenames/keyring service
are preserved; old caches already losing number bytes need an online refresh.

Deliberate corrections: invalid defaults never enable access, malformed times/
identity fail closed, pinned key IDs must match their actual key, and loopback
HTTP needs explicit allow_loopback_http=True. Python 3.9/3.10 are no longer in
the candidate range. cryptography 50.0.2+ below 51 is required after audit;
Intel macOS/32-bit Windows wheels are no longer supplied upstream.

AsyncLicenseClient wraps an existing client; no new activation is created.
The candidate remains 1.1.0rc1 until owner release approval.
