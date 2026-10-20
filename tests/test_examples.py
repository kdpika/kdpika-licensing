"""Execute shipped examples with real signed mock responses, never a network."""

import asyncio
import importlib
from pathlib import Path

import pytest

from kdpika_licensing import LicenseClient, LicenseResult


@pytest.fixture
def examples(monkeypatch, tmp_path, session):
    monkeypatch.syspath_prepend(str(Path(__file__).parents[1] / "examples"))
    for name, value in {
        "KDP_APP_ID": "app_synthetic",
        "KDP_STATE_DIR": str(tmp_path),
        "KDP_LICENSE_KEY": "SYNTHETIC-NOT-A-REAL-KEY",
        "KDP_CUSTOMER_EMAIL": "tester@example.invalid",
        "KDP_BASE_URL": "https://licenses.example.invalid",
    }.items():
        monkeypatch.setenv(name, value)
    _, transport, now = session
    common = importlib.import_module("_common")
    monkeypatch.setattr(
        common,
        "LicenseClient",
        lambda **kwargs: LicenseClient(**kwargs, transport=transport, clock=lambda: now[0]),
    )
    return lambda name: importlib.import_module(name), transport


@pytest.mark.parametrize("name", ["basic", "features", "offline", "errors", "async_usage", "members"])
def test_example_success(examples, name, capsys):
    load, _ = examples
    assert load(name).main() == 0
    output = capsys.readouterr().out
    assert "SYNTHETIC-NOT-A-REAL-KEY" not in output and "act_synthetic" not in output


@pytest.mark.parametrize("name", ["basic", "features", "offline", "errors", "async_usage"])
def test_example_refusal(examples, name):
    load, transport = examples
    transport.status = "LICENSE_REVOKED"
    assert load(name).main() == 1


def test_session_full_lifecycle(examples):
    load, _ = examples
    cli = load("session")
    for action in ["status", "activate", "check", "validate", "deactivate", "clear-local"]:
        assert cli.main([action]) == 0
    assert cli.main(["check"]) == 1


def test_feature_defaults_do_not_enable_example(examples):
    load, _ = examples
    result = LicenseResult(False, "offline")
    assert load("features").permissions(result) == {"pdf_export": False, "seat_count": None}


def test_qt_example_uses_guarded_dialog(examples, monkeypatch):
    load, _ = examples
    ui = load("pyqt_activation")
    monkeypatch.setattr(
        ui, "show_activation_dialog", lambda client, **kw: client.activate("SYNTHETIC-NOT-A-REAL-KEY")
    )
    assert ui.main() == 0


def test_backend_protected_route(examples, monkeypatch):
    flask = pytest.importorskip("flask")
    load, transport = examples
    backend = load("backend_flask")
    app = backend.create_app()
    assert isinstance(app, flask.Flask)
    with app.test_client() as client:
        assert client.post("/export").status_code == 403  # Feature absent: deny.
        transport.changes = {"features": {"pdf_export": True}}
        # Fresh validation, never grant based on changing local metadata.
        shared = load("_common").configured_client()
        assert shared.validate().valid
        assert client.post("/export").status_code == 200
        transport.status = "LICENSE_REVOKED"
        assert not shared.validate().valid
        assert client.post("/export").status_code == 403


def test_async_example_is_awaitable(examples):
    load, _ = examples
    assert asyncio.run(load("async_usage").example()) == 0
