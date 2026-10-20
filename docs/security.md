# Security

The SDK authenticates Ed25519 data, checks origin-sourced/pinned key identity,
product/environment/installation binding and signed access policy. It never
offers a switch disabling signatures or TLS. Only explicit loopback HTTP is
permitted for local tests. Redirects are not followed with activation credentials.

All responses/cache JSON are bounded to 1 MiB/64 levels. Ambiguous duplicate
properties, malformed Unicode, non-finite numbers and noncanonical base64url
are refused. PHP signature vectors and cache round trips are regression-tested.

Default trust is the configured HTTPS origin's public-key endpoint, not a key
embedded in a response. A configured pin never changes automatically. Unknown
keys may be refetched only online, rate-bounded; no historical-key overlap is
invented when the server does not provide one.

Local machine owners can patch applications/clocks/state. Private fallback
files are not encrypted vaults. The SDK is not a payment verifier, penetration
test certificate, authentication system or guarantee of tamper-proof access.
See [Offline policy](offline.md) and [Storage](storage.md).

Report suspected vulnerabilities privately to hi@kdpika.com. Include runtime/
SDK version, a synthetic reproduction and safe request ID only. No customer
keys/tokens/payloads or exploit details in public issues. The repository's
SECURITY.md sets the same policy; no support/security SLA is invented.
