# Changelog

## 1.1.5 — 2026-10-20

Move macOS CI to the supported Intel runner pool and build the same cryptography
dependency with Rust/OpenSSL 3 after repeated arm64 runner-acquisition failures.
All native test combinations, audits and protected publication gates remain.

## 1.1.4 — unpublished release preparation, 2026-10-20

Audit the exact installed third-party dependency inventory without querying the
unpublished SDK itself. Audit scope is recorded; all audit failures still block
publication. No SDK runtime changes.

## 1.1.3 — unpublished release preparation, 2026-10-20

- Pin native macOS CI to `macos-15` arm64 following hosted runner allocation
  failures. Core SDK behavior, required tests and publishing protections stay
  unchanged. Earlier unpublished tags are preserved.

## 1.1.1 — unpublished release preparation, 2026-10-20

- Preserve approved LICENSE bytes across operating systems using Git LF rules.
- Supersedes the unpublished 1.1.0 attempt without rewriting its tag or changing
  the SDK runtime. See PyPI for registry availability.

## 1.1.0 — unpublished release preparation, 2026-10-20

### Fixed
- PHP signed JSON numbers/Unicode and cache verification.
- Fail-closed feature/default helpers, strict time/binding/key policy.
- Bounded transport and private atomic synchronized state.
- Windows test harness compatibility without changing SDK runtime behavior.

### Added
- kdpika_licensing namespace, compatibility warning shims, async adapter, typing.
- Source-verified SDK guides, generated reference and tested Sandbox examples.
- Candidate quality/CI/OIDC release preparation with explicit owner gates.

### Changed
- The owner selected MIT for the Python SDK and its included documentation.
  Separate platform/backend/service access is not included in that grant.

### Verification
Publication requires successful release checks and protected environment approval.
See PyPI for actual uploaded versions and the release workflow for OS results.
Native GUI/vault/packaged-app acceptance remains separate from core CI.

The included project CHANGELOG.md retains detailed local 1.0.0 observations.
