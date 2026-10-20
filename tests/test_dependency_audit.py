"""Audit the complete installed dependency inventory without querying our candidate."""

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def audit_module(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).parents[1] / "tools"))
    return importlib.import_module("audit_dependencies")


@pytest.mark.parametrize("returncode", [0, 1, 2])
def test_all_dependencies_retained_and_audit_failure_propagates(
    audit_module, monkeypatch, tmp_path, returncode
):
    inventory = [
        SimpleNamespace(metadata={"Name": "KDPika_Licensing"}, version="1.2.3"),
        SimpleNamespace(metadata={"Name": "cryptography"}, version="50.0.2"),
        SimpleNamespace(metadata={"Name": "cffi"}, version="2.0.0"),
        SimpleNamespace(metadata={"Name": "pip"}, version="26.2.1"),
    ]

    def installed(*, path):
        assert path == ["synthetic/site-packages"]
        return inventory

    output = tmp_path / "audit.json"

    def run(command, *, check):
        assert check is False
        requirements = Path(command[command.index("--requirement") + 1]).read_text().splitlines()
        assert requirements == ["cffi==2.0.0", "cryptography==50.0.2", "pip==26.2.1"]
        assert {"--strict", "--no-deps", "--disable-pip"} <= set(command)
        assert "--ignore-vuln" not in command
        output.write_text('{"dependencies": [], "fixes": []}')
        return SimpleNamespace(returncode=returncode)

    monkeypatch.setattr(audit_module, "distributions", installed)
    monkeypatch.setattr(audit_module.subprocess, "run", run)
    assert audit_module.audit("synthetic/site-packages", output) == returncode
    scope = json.loads(output.read_text())["audit_scope"]
    assert scope["excluded_own_candidate"] == [{"name": "kdpika-licensing", "version": "1.2.3"}]
    assert len(scope["installed_third_party_requirements"]) == 3


def test_empty_inventory_fails_closed(audit_module, monkeypatch, tmp_path):
    monkeypatch.setattr(audit_module, "distributions", lambda **kwargs: [])
    with pytest.raises(ValueError, match="No installed third-party"):
        audit_module.audit("synthetic/site-packages", tmp_path / "audit.json")
