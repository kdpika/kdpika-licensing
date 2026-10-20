# Candidate 1.1.0rc1 — migration and security changes

This is an **unpublished Phase 1 candidate**, not a PyPI release announcement.
The complete PyPI README, rendered documentation and publishing automation are
Phase 2 work, pending owner review. No `pip install` registry claim is made here.

## Imports and private modules

Use `from kdpika_licensing import LicenseClient, LicenseResult`.
The old `license_sdk` import and submodules continue with DeprecationWarning.
Only the package-root exports are stable. `HttpResponse`, transport, storage
and client.local/client.credentials/client.transport are compatibility/internal
surfaces. For a custom transport, use `_transport.Transport` and
`models.HttpResponse.from_bytes` and pin the SDK version; do not use an ordinary
JSON decoder that loses signed numeric spellings.

Candidate distribution is `kdpika-licensing`; import is `kdpika_licensing`.
Uninstall the old local distribution before installing this candidate to avoid
two distributions owning `license_sdk`. Python 3.11–3.14 is the candidate range;
3.9/3.10 consumers must stay on their assessed old release or update Python.
Version/name/license/repository remain owner approval decisions.

The dependency audit rejected the initially assessed cryptography 46.0.7;
the candidate now requires `cryptography>=50.0.2,<51`. Its upstream 49+
release no longer supplies Intel macOS or 32-bit Windows wheels. Those users
must assess a supported environment or a native source build; no automatic
fallback to an advisory-affected version is provided. Only arm64 macOS has
been executed here. See the [upstream changelog](https://cryptography.io/en/50.0.2/changelog/).

## State compatibility

Default directory, namespace hash, random installation ID, keyring service ID,
file names and `version: 1` state are unchanged. No automatic seat reset.
The new decoder retains each numeric token (ordinary int/float subclasses) and
the writer preserves it. Older caches that already lost signature bytes cannot
be repaired offline; a fresh authenticated online decision is required. Never
disable signature checking or delete identity to get around this.

Private POSIX directories/files must be owner-only. Corrupted signed cache can
recover online; a corrupted identity stops with StorageError instead of silently
consuming another seat. A `.sdk.lock` file adds bounded local process/thread
serialization, not a new token format. Do not use network filesystems or share
one state path between users. Windows requires a user-only ACL; native Windows
and Linux/keyring tests must be run before claiming those OS integrations tested.

## Deliberate fail-closed behavior corrections

Result `features` is empty on a refused, unsigned or time-invalid decision.
`feature(..., default=True)` still returns False on failure;
`feature_value(..., default=100)` returns None on failure. These changes close
an unsafe old behavior; they are not deprecated access bypasses. Client helpers
call check() again. Retained results re-check expiry and the applicable deadline at helper use: grace for cache/offline, next-validation for a fresh online result. Zero offline grace never prevents a fresh online decision, but prevents later cached/offline use.
Treat result.valid as a decision at the check time, not a lifetime capability.

The safe order is valid **and** signature_valid, then required-feature checks.
Successful deactivate has valid=True for the release acknowledgement but
signature_valid=False and cannot enable features. String 'false' does not act
as an enabled boolean feature. Returned feature mappings are detached copies.

Missing/malformed signed server/next/grace time or expiry fails closed. Lifetime
requires explicit expires_at=null, never a malformed date. Aware clock required;
300-second rollback tolerance retained. Grace is an absolute signed deadline,
not an interval started after a connection error.

## Signing key changes and trust

The default trust source is the configured HTTPS origin's public-key endpoint.
This is server-authenticated TLS trust, not a key taken from the envelope.
Key IDs must match SHA-256-derived Ed25519 identity. A changed ID is refetched
only online, at most once per ten seconds per client (transport retries that
safe GET once). Unknown keys offline fail closed. No historical key overlap
can be invented when the server does not publish one. A pinned key never changes
automatically; KEY_ROTATION_REQUIRED asks for a publisher-controlled update.

## Network, storage and concurrency

HTTPS is mandatory. Local loopback HTTP now requires
`allow_loopback_http=True` explicitly; no environment variable disables TLS.
Redirects are not followed, so bearer credentials do not cross origins.
JSON is bounded to 1 MiB/64 levels; duplicate names, non-finite numbers, malformed
UTF-8/surrogates and trailing content are rejected. Public-key GET has one bounded
retry with jitter and short Retry-After handling; POST mutations are never retried.
No automatic rate-limit retry loop. Errors expose safe messages/request_id only;
upstream message strings are not echoed. repr excludes payloads and credentials.

`AsyncLicenseClient(existing_client)` runs the same synchronized core using
asyncio.to_thread. Cancellation does not stop a running HTTP request. Keep the
same installation and reconcile uncertain outcomes instead of blind retries.
The optional Qt UI is not a new async GUI framework; activation remains a
blocking dialog operation and needs native GUI testing in Phase 2.

No CLI entry point is installed in Phase 1: existing session examples remain
the safe starting point until their full command/secret-handling tests in Phase 2.
