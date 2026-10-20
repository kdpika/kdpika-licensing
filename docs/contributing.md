# Contributing

Use the [SDK repository](https://github.com/kdpika/kdpika-licensing) if you have
access; it is private. Otherwise contact hi@kdpika.com. Follow the included
CODE_OF_CONDUCT.md; send security reports privately, not in public issues.

Install .[dev,docs,test] in a private virtualenv. Run Ruff lint/format, strict
mypy, pytest with coverage, tox and mkdocs build --strict. Use only synthetic
Sandbox data and ephemeral signing keys. No secrets/customer payloads in issues.

Preserve API-v1 signing/state compatibility. Every fix needs a regression test,
migration note for behavior changes and honest target-platform results.
Security reports go privately to hi@kdpika.com. Publication/push/tag actions
require the owner's explicit approval; see [Release process](release.md).
