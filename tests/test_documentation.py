"""Run public docstrings and shipped README/guide code with signed mock transport."""

import asyncio
import doctest
import importlib
import re
from pathlib import Path

import pytest

import kdpika_licensing
from kdpika_licensing import LicenseClient

ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize("name", ["client", "models", "errors", "async_client"])
def test_public_docstring_examples(name):
    module = importlib.import_module("kdpika_licensing." + name)
    result = doctest.testmod(module)
    assert result.failed == 0 and result.attempted > 0


@pytest.mark.parametrize("document", ["README.md", "docs/getting-started.md"])
def test_markdown_python_blocks(document, monkeypatch, tmp_path, session):
    _, transport, now = session
    monkeypatch.setenv("KDP_APP_ID", "app_synthetic")
    monkeypatch.setenv("KDP_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("KDP_LICENSE_KEY", "SYNTHETIC-NOT-A-REAL-KEY")
    monkeypatch.setenv("KDP_CUSTOMER_EMAIL", "tester@example.invalid")
    monkeypatch.setattr(
        kdpika_licensing,
        "LicenseClient",
        lambda **kw: LicenseClient(**kw, prefer_keyring=False, transport=transport, clock=lambda: now[0]),
    )
    blocks = re.findall(r"~~~python\n(.*?)\n~~~", (ROOT / document).read_text(encoding="utf-8"), re.S)
    assert blocks
    namespace = {}
    for block in blocks:
        exec(compile(block, document, "exec"), namespace)
    assert namespace["result"].valid and namespace["result"].signature_valid
    assert transport.calls


def test_async_guide_code(session):
    make, _, _ = session
    text = (ROOT / "docs/guides/async.md").read_text(encoding="utf-8")
    block = re.search(r"~~~python\n(.*?)\n~~~", text, re.S).group(1)
    namespace = {}
    exec(compile(block, "async guide", "exec"), namespace)
    assert not asyncio.run(namespace["permitted"](make()))  # Missing activation denies.


def test_readme_faq_and_constructor_parameters_are_present():
    import inspect

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert len(re.findall(r"^### \d+\.", readme, re.M)) >= 25
    for name in inspect.signature(LicenseClient).parameters:
        assert name in readme
    assert "signature_valid" in readme
    assert "MIT License" in readme
    assert "Copyright (c) 2026 KHALED AL HARAZI" in readme
    from kdpika_licensing.client import _MESSAGES

    assert all(code in readme for code in _MESSAGES)


def test_private_reports_not_in_public_site():
    site = ROOT / "site"
    if not site.exists():
        pytest.skip("Run mkdocs build --strict for generated-site checks")
    assert not (site / "internal").exists()
    assert not list(site.rglob("dependency-audit*.json"))
