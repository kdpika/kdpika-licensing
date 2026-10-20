# Contributing

The public SDK repository is https://github.com/kdpika/kdpika-licensing.
It does not contain the separately hosted platform/backend. Contact
hi@kdpika.com if needed; report security issues privately using SECURITY.md.

From the SDK root in a private active virtualenv:
~~~bash
python -m pip install -e '.[dev,docs,test]'
ruff check src tests tools examples
ruff format --check src tests tools examples
mypy --strict src
python -m pytest --cov
tox -e py311,py312,py313,py314
mkdocs build --strict
python -m build
python -m twine check dist/*
python tools/verify_artifacts.py
python tools/audit_dependencies.py
python tools/audit_dependencies.py --tooling
~~~

Use synthetic fixtures and ephemeral test keys only. Default tests cannot open
sockets; optional live Sandbox tests need explicit opt-in. Preserve API-v1
shapes/signing/state semantics, add regressions and document compatibility
changes. Do not update hosted downloads or publish/tag/push without owner approval.

Local pre-commit hooks require Ruff on PATH; running pre-commit install is an
optional developer action, not performed automatically. Follow CODE_OF_CONDUCT.md.
Contributions must be compatible with the project's MIT License. Only submit
code and documentation you have permission to share; no separate CLA is imposed.
