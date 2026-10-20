"""Atomic private storage, corruption and process/thread serialization."""

import importlib
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock

import pytest

from kdpika_licensing._storage import (
    CredentialStore,
    LocalStateStore,
    default_storage_root,
    storage_namespace,
)
from kdpika_licensing.errors import StorageError


@pytest.fixture
def local(tmp_path):
    return LocalStateStore(tmp_path, "synthetic")


def test_local_identity_cache_and_token_lifecycle(local):
    first = local.installation_id()
    assert local.installation_id() == first
    assert local.load_fallback_token() is None and local.load_state() == {}
    local.save_fallback_token("act_synthetic_token")
    assert local.load_fallback_token() == "act_synthetic_token"
    local.save_state({"version": 1})
    assert local.load_state() == {"version": 1}
    if os.name != "nt":
        assert local.root.stat().st_mode & 0o777 == 0o700
        for path in [local.identity_path, local.state_path, local.token_path]:
            assert path.stat().st_mode & 0o777 == 0o600
    local.clear_state()
    local.clear_fallback_token()
    assert local.load_state() == {} and local.load_fallback_token() is None


@pytest.mark.parametrize(
    "content", [b"[]", b"broken", b'{"installation_id":"wrong"}', b'{"installation_id":"lmp-install-wrong"}']
)
def test_corrupted_identity_never_silently_consumes_new_seat(local, content):
    local._atomic_write(local.identity_path, content)
    with pytest.raises(StorageError):
        local.installation_id()
    assert local.identity_path.read_bytes() == content


@pytest.mark.parametrize("content", [b"bad", b"\xff", b"act_ secret", b""])
def test_corrupted_token_is_not_used(local, content):
    local._atomic_write(local.token_path, content)
    with pytest.raises(StorageError):
        local.load_fallback_token()


def test_private_permissions_fail_closed(local):
    if os.name == "nt":
        pytest.skip("POSIX permissions only")
    local.save_fallback_token("act_synthetic_token")
    local.token_path.chmod(0o644)
    with pytest.raises(StorageError):
        local.load_fallback_token()


def test_symlinks_are_not_followed(local, tmp_path):
    if os.name == "nt":
        pytest.skip("POSIX O_NOFOLLOW semantics; Windows reparse/ACL protection is not certified")
    outside = tmp_path / "outside"
    outside.write_text("private")
    local.token_path.symlink_to(outside)
    with pytest.raises(StorageError):
        local.load_fallback_token()
    alias = tmp_path / "alias"
    alias.symlink_to(outside)
    with pytest.raises(StorageError):
        LocalStateStore(tmp_path, "alias")


def test_size_limit(local):
    local._atomic_write(local.state_path, b" " * 1048577)
    with pytest.raises(StorageError):
        local.load_state()


def test_atomic_failure_does_not_clobber_old_state(local, monkeypatch):
    local.save_state({"safe": 1})

    def fail(*args):
        raise OSError("PRIVATE")

    monkeypatch.setattr("kdpika_licensing._storage.os.replace", fail)
    with pytest.raises(StorageError) as caught:
        local.save_state({"safe": 2})
    assert "PRIVATE" not in str(caught.value) and local.load_state() == {"safe": 1}
    assert not list(local.root.glob("signed-state.json.*"))


def test_permission_failure_not_silently_swallowed(tmp_path, monkeypatch):
    if os.name == "nt":
        pytest.skip("POSIX chmod error handling; Windows needs private user ACLs")
    monkeypatch.setattr(Path, "chmod", Mock(side_effect=PermissionError("PRIVATE")))
    with pytest.raises(StorageError):
        LocalStateStore(tmp_path, "new")


def test_thread_and_subprocess_identity_is_stable(tmp_path):
    def create(_):
        return LocalStateStore(tmp_path, "parallel").installation_id()

    with ThreadPoolExecutor(max_workers=8) as pool:
        values = list(pool.map(create, range(16)))
    assert len(set(values)) == 1
    code = 'from kdpika_licensing._storage import LocalStateStore;from pathlib import Path;import sys;print(LocalStateStore(Path(sys.argv[1]),"process").installation_id())'
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", code, str(tmp_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(4)
    ]
    ids = []
    for process in processes:
        stdout, stderr = process.communicate(timeout=20)
        assert process.returncode == 0, stderr
        ids.append(stdout.strip())
    assert len(set(ids)) == 1


def test_reentrant_lock_and_failed_acquisition(local, monkeypatch):
    with local.lock():
        with local.lock():
            assert local._depth == 2
    local._thread_lock = Mock()
    local._thread_lock.acquire.return_value = False
    with pytest.raises(StorageError):
        with local.lock():
            pass


def test_process_lock_timeout_is_bounded(local, monkeypatch):
    tick = iter([0, 10])
    monkeypatch.setattr("kdpika_licensing._storage.time.monotonic", lambda: next(tick))
    monkeypatch.setattr(local, "_file_lock", Mock(side_effect=OSError("PRIVATE")))
    with pytest.raises(StorageError):
        with local.lock():
            pass
    assert local._depth == 0


def test_lock_wait_then_success(local, monkeypatch):
    monkeypatch.setattr("kdpika_licensing._storage.time.sleep", lambda _: None)
    lock = Mock(side_effect=[BlockingIOError(), None, None])
    monkeypatch.setattr(local, "_file_lock", lock)
    with local.lock():
        pass
    assert lock.call_count == 3


def test_unlock_error_releases_thread_lock_and_sanitizes(local, monkeypatch):
    monkeypatch.setattr(local, "_file_lock", Mock(side_effect=[None, OSError("PRIVATE")]))
    with pytest.raises(StorageError) as caught:
        with local.lock():
            pass
    assert "PRIVATE" not in str(caught.value)
    assert local._thread_lock.acquire(blocking=False)
    local._thread_lock.release()


def test_keyring_unavailable_or_disabled_uses_explicit_file(local, monkeypatch):
    monkeypatch.setattr(importlib, "import_module", Mock(side_effect=ImportError()))
    credentials = CredentialStore(local, "service", "synthetic", True)
    assert credentials.security == "permission-protected-file"
    credentials.save("act_synthetic_token")
    assert credentials.load() == "act_synthetic_token"
    credentials.clear()
    assert credentials.load() is None


def backend(monkeypatch):
    module = Mock()
    module.get_keyring.return_value.priority = 1
    module.get_password.return_value = None
    monkeypatch.setattr(importlib, "import_module", lambda _: module)
    return module


def test_keyring_round_trip_and_fallback_file_removed(local, monkeypatch):
    module = backend(monkeypatch)
    credentials = CredentialStore(local, "service", "synthetic")
    local.save_fallback_token("act_old_synthetic")
    credentials.save("act_new_synthetic")
    assert credentials.security == "os-keyring" and not local.token_path.exists()
    module.get_password.return_value = "act_new_synthetic"
    assert credentials.load() == "act_new_synthetic"
    credentials.clear()
    assert module.delete_password.call_count == 1


def test_keyring_write_failure_without_old_secret_can_fallback(local, monkeypatch):
    module = backend(monkeypatch)
    module.set_password.side_effect = RuntimeError("PRIVATE")
    credentials = CredentialStore(local, "service", "synthetic")
    credentials.save("act_synthetic_token")
    assert credentials.security == "permission-protected-file" and credentials.load() == "act_synthetic_token"


def test_keyring_failures_cannot_resurrect_old_credential(local, monkeypatch):
    module = backend(monkeypatch)
    credentials = CredentialStore(local, "service", "synthetic")
    module.set_password.side_effect = RuntimeError()
    module.get_password.return_value = "act_old_synthetic"
    with pytest.raises(StorageError):
        credentials.save("act_new_synthetic")
    module.delete_password.side_effect = RuntimeError()
    with pytest.raises(StorageError):
        credentials.clear()
    module.get_password.side_effect = RuntimeError()
    with pytest.raises(StorageError):
        credentials.load()
    with pytest.raises(StorageError):
        credentials.save("act_new_synthetic")


def test_keyring_read_error_only_falls_back_when_file_exists(local, monkeypatch):
    module = backend(monkeypatch)
    credentials = CredentialStore(local, "service", "synthetic")
    module.get_password.side_effect = RuntimeError()
    local.save_fallback_token("act_synthetic_token")
    assert credentials.load() == "act_synthetic_token" and credentials.security == "permission-protected-file"


def test_keyring_bad_return_denied(local, monkeypatch):
    module = backend(monkeypatch)
    module.get_password.return_value = 123
    with pytest.raises(StorageError):
        CredentialStore(local, "service", "synthetic").load()


@pytest.mark.parametrize("system", ["Darwin", "Windows", "Linux"])
def test_default_paths_do_not_change_namespace(system, monkeypatch):
    monkeypatch.setattr("kdpika_licensing._storage.platform.system", lambda: system)
    monkeypatch.setenv("APPDATA", "/synthetic-user/appdata")
    monkeypatch.setenv("XDG_DATA_HOME", "/synthetic-user/data")
    root = default_storage_root("Example App")
    assert "Example-App" in str(root)
    assert len(storage_namespace("https://example.invalid", "app_synthetic", "SANDBOX")) == 20
    assert storage_namespace("https://example.invalid/", "app_synthetic", "sandbox") == storage_namespace(
        "https://example.invalid", "app_synthetic", "SANDBOX"
    )
