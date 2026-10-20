"""Additional refusal, storage and result boundaries; no live service."""

import importlib
import warnings
from datetime import timedelta
from unittest.mock import Mock

import pytest
from test_security import NOW, activate, denied

from kdpika_licensing import LicenseResult, StorageError
from kdpika_licensing.models import HttpResponse


def test_zero_offline_grace_permits_fresh_online_but_not_cached(session):
    make, transport, now = session
    transport.changes = {"offline_grace_until": NOW.isoformat()}
    client = make()
    result = activate(client)
    assert result.feature("export")
    now[0] += timedelta(seconds=1)
    transport.network = True
    denied(client.check())


def test_rejected_activation_never_keeps_untrusted_token(session):
    make, transport, _ = session
    transport.bad_signature = True
    client = make()
    denied(client.activate("SYNTHETIC-NOT-A-REAL-KEY"))
    assert not client.activated and transport.calls[-1][1].endswith("deactivate")


@pytest.mark.parametrize(
    "body",
    [
        {"success": True},
        {"success": True, "activation_token": "bad", "license": {}},
        {"success": True, "activation_token": "act_synthetic", "license": []},
    ],
)
def test_incomplete_activation_fails(session, body):
    make, transport, _ = session
    transport.override = HttpResponse(200, {}, body)
    denied(make().activate("SYNTHETIC-NOT-A-REAL-KEY"))


def test_incomplete_validation_clears_old_grant(session):
    make, transport, _ = session
    client = make()
    activate(client)
    transport.override = HttpResponse(200, {}, {"success": True})
    denied(client.validate())
    transport.network = True
    denied(client.check())


def test_deactivation_failure_preserves_recovery_state(session):
    make, transport, _ = session
    client = make()
    activate(client)
    transport.network = True
    denied(client.deactivate())
    assert client.activated
    transport.network = False
    transport.status = "RATE_LIMITED"
    denied(client.deactivate())
    assert client.activated
    transport.status = None
    transport.override = HttpResponse(200, {}, {"success": True})
    denied(client.deactivate())
    assert client.activated


def test_storage_failure_cannot_return_access_or_claim_token_presence(session, monkeypatch):
    make, transport, _ = session
    client = make()
    activate(client)
    monkeypatch.setattr(client._credentials, "load", Mock(side_effect=StorageError()))
    assert not client.activated
    denied(client.check())


def test_activation_storage_failure_attempts_server_cleanup(session, monkeypatch):
    make, transport, _ = session
    client = make()
    monkeypatch.setattr(client._credentials, "save", Mock(side_effect=StorageError()))
    denied(client.activate("SYNTHETIC-NOT-A-REAL-KEY"))
    assert transport.calls[-1][1].endswith("deactivate")


def test_invalid_signed_checkpoint_never_becomes_ordinary_cache(session):
    make, _, _ = session
    client = make()
    activate(client)
    state = client._local.load_state()
    state["last_seen_at"] = "malformed"
    client._local.save_state(state)
    denied(client.check())


def test_unknown_key_offline_never_fetches_network(session):
    make, transport, _ = session
    client = make()
    activate(client)
    state = client._local.load_state()
    state.pop("verification_key")
    state["signed_license"]["key_id"] = "ed25519_unknown"
    client._local.save_state(state)
    before = len(transport.calls)
    transport.network = True
    denied(client.validate())
    assert not any(p.endswith("public-key") for _, p in transport.calls[before:])


def test_result_public_properties_and_rechecks(session):
    make, _, now = session
    result = activate(make())
    assert result.status == "active" and result.license_id == "lic_synthetic"
    assert result.expires_at and result.offline_grace_until
    assert result.feature("not-present", True)
    now[0] = NOW.replace(tzinfo=None)
    assert not result.feature("export")
    malformed = LicenseResult(True, "cache", {"status": "active", "server_time": "bad"}, signature_valid=True)
    assert not malformed.feature("export", True)
    assert LicenseResult(False, "local").license_id is None
    assert LicenseResult(False, "local").offline_grace_until is None


def test_old_module_paths_and_deprecation_are_compatible():
    import kdpika_licensing

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        module = importlib.import_module("license_sdk")
        importlib.reload(module)
        assert module.LicenseClient is kdpika_licensing.LicenseClient
        assert any(issubclass(w.category, DeprecationWarning) for w in records)
    for name in ["client", "models", "errors", "storage", "transport", "ui"]:
        assert importlib.import_module("license_sdk." + name)


def test_confirmed_deactivation_cannot_leave_cache_on_keyring_delete_failure(session, monkeypatch):
    make, _, _ = session
    client = make()
    activate(client)
    monkeypatch.setattr(client._credentials, "clear", Mock(side_effect=StorageError()))
    denied(client.deactivate())
    assert client._local.load_state() == {}


def test_atomic_activation_state_failure_cleans_old_cache(session, monkeypatch):
    make, transport, _ = session
    client = make()
    activate(client)
    monkeypatch.setattr(client._local, "save_state", Mock(side_effect=StorageError()))
    denied(client.activate("SYNTHETIC-NOT-A-REAL-KEY"))
    assert client._local.load_state() == {}
    assert transport.calls[-1][1].endswith("deactivate")


@pytest.mark.parametrize(
    "code",
    [
        "DEVICE_LIMIT_REACHED",
        "ACTIVATION_LIMIT_REACHED",
        "APP_VERSION_NOT_SUPPORTED",
        "DEVICE_NOT_AUTHORIZED",
        "LICENSE_PENDING",
        "INVALID_REQUEST",
        "PLAN_NOT_FOUND",
    ],
)
def test_actual_api_refusal_codes_remain_safe_and_fail_closed(session, code):
    make, transport, _ = session
    client = make()
    activate(client)
    transport.status = code
    result = client.validate()
    denied(result)
    assert result.error_code == code
    assert result.message
    transport.network = True
    denied(client.check())
