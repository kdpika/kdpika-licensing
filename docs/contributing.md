# Contributing

Use the public [SDK repository](https://github.com/kdpika/kdpika-licensing)
for non-sensitive SDK contributions. It does not contain the platform/backend.
Follow CODE_OF_CONDUCT.md; send security reports privately to hi@kdpika.com,
not in public issues.

Install .[dev,docs,test] in a private virtualenv. Run Ruff lint/format, strict
mypy, pytest with coverage, tox and mkdocs build --strict. Use only synthetic
Sandbox data and ephemeral signing keys. No secrets/customer payloads in issues.

Preserve API-v1 signing/state compatibility. Every fix needs a regression test,
migration note for behavior changes and honest target-platform results.
Security reports go privately to hi@kdpika.com. Publication/push/tag actions
require the owner's explicit approval; see [Release process](release.md).
