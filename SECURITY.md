# Security policy

## Supported scope
The current prepared Python candidate is 1.1.0rc1; it has not been published.
No historical release-support schedule, vulnerability-free certification or
security-response SLA is promised. Confirm the owner-approved version before use.

## Reporting privately
Email hi@kdpika.com with SDK/Python/OS versions, a synthetic minimal reproduction
and safe request_id if available. Never attach keys, activation tokens, state
files, customer payloads, credentials or exploit details to a public issue.

We will assess reports through the published contact; coordinated disclosure
timing is agreed per report rather than invented as a fixed guarantee.

## Threat boundary
Ed25519 authentication is not anti-tampering against a machine owner. Keep
management API keys on a trusted server, preserve TLS/signature verification,
and protect state with OS permissions/ACLs or an optional usable native vault.
Never silently downgrade pins, blindly retry mutations or grant offline access
after an authoritative refusal. SECURITY.md changes do not alter service terms.
