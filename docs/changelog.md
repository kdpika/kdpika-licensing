# Changelog

## 1.1.0 — 2026-10-20

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
