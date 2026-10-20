# Changelog

Notable changes follow Keep a Changelog categories. API v1 and SDK package
versions are independent. The candidate below has not been published.

## [Unreleased] — 1.1.0rc1 candidate, 2026-10-20

### Fixed

- Preserve signed JSON wire number tokens through HTTP/cache round trips and
  escape U+2028/U+2029; strict duplicate/UTF-8/base64url/depth/size checks.
- Gate feature helpers on a verified valid current result, including expiry,
  signed grace, binding and clock failures; no enabling failure defaults.
- Bound HTTPS requests and public-key GET retries; refuse redirects and
  never retry uncertain activation/deactivation POSTs.
- Validate signed timestamps and key-derived IDs; pinned keys never rotate
  silently. Safe upstream messages and repr without payload/credential values.
- Atomic private version-1 storage, bounded process/thread locks, no new identity
  after corruption, and explicit keyring failure/fallback behavior.

### Added

- `kdpika_licensing` public package and an async adapter using the same core.
- Strict typing, py.typed, shared PHP-signed fixtures, regression/property tests,
  ruff/mypy/pytest/tox tooling and a Phase 1 migration/security audit.
- Complete candidate README with 35 FAQ entries, source-generated API reference,
  strict-build MkDocs guides, safe runnable Sandbox examples and example/doctest checks.
- Project security/contribution/conduct policies and version-derived artifact checks.
- SHA-pinned dedicated-repository CI templates (12 OS/Python combinations) and
  OIDC TestPyPI/PyPI release routing; owner/repository/tag/license gates stay closed.
- Separate installed-base and dedicated-tooling advisory audits; require pytest
  9.0.3+ after the initial tooling audit found the old temporary-directory advisory.

### Changed

- Candidate distribution `kdpika-licensing`; `license_sdk` remains a deprecated
  compatibility shim. Storage namespace, filenames and keyring service unchanged.
- Candidate Python support 3.11–3.14; local loopback HTTP needs explicit opt-in.
- Inconsistent pinned IDs are now configuration errors before any HTTP call.
- Require cryptography 50.0.2+ (below 51) after dependency auditing; upstream
  no longer supplies Intel macOS or 32-bit Windows wheels. Native compatibility
  beyond the executed arm64 macOS matrix remains unverified.

### Not released

Owner approval, final SDK usage/redistribution license and repository identity
are pending. Documentation/examples/publishing automation are prepared and locally
verified as described in the final report; remote CI/OIDC publication is not run.
No PyPI/TestPyPI upload, public tag, remote push or hosting deployment occurred.

## 1.0.0 — observed current source, 2026-10-17

This is the version recorded in current package/project metadata (PHP uses the
existing versioned download label). It is not a reconstructed original release
date, a published registry release or an invented earlier-version history.

- Added complete source-install, lifecycle, storage/offline and known-limit
  documentation, license-information notice and runnable example links.
- Preserved runtime implementation, public APIs, response handling and package
  identity. Documentation changes do not silently fix known signing/cache gaps.
- PHP includes a new package-local standalone test entry; its legacy repository
  test remains unchanged and still assumes the repository-root autoload layout.

Future entries must identify the exact version, verified changes, compatibility
impact and tests. API v1 and SDK package versions are independent.
