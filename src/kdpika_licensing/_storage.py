"""Private version-1 state layout with atomic writes and bounded process locks."""

from __future__ import annotations

import hashlib
import importlib
import os
import platform
import stat
import tempfile
import threading
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from ._json import MAX_BYTES, canonical, loads
from .errors import StorageError

_LOCKS: dict[str, threading.RLock] = {}
_REGISTRY = threading.Lock()


def default_storage_root(application_name: str) -> Path:
    safe = (
        "".join(c if c.isalnum() or c in "-_" else "-" for c in application_name).strip("-") or "licensed-app"
    )
    system = platform.system().lower()
    if system == "darwin":
        return Path.home() / "Library" / "Application Support" / safe / "License"
    if system == "windows":
        return Path(os.environ.get("APPDATA", str(Path.home()))) / safe / "License"
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))) / safe / "license"


def storage_namespace(base_url: str, app_id: str, environment: str) -> str:
    value = "|".join([base_url.rstrip("/").lower(), app_id, environment.upper()])
    return hashlib.sha256(value.encode()).hexdigest()[:20]


class LocalStateStore:
    def __init__(self, root: Path, namespace: str) -> None:
        self.root = Path(root) / namespace
        try:
            if self.root.is_symlink():
                raise StorageError()
            self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
            self._chmod(self.root, 0o700)
        except OSError:
            raise StorageError() from None
        self.identity_path = self.root / "installation.json"
        self.state_path = self.root / "signed-state.json"
        self.token_path = self.root / "activation-token"
        self._depth = 0
        with _REGISTRY:
            self._thread_lock = _LOCKS.setdefault(str(self.root.resolve()), threading.RLock())

    @contextmanager
    def lock(self) -> Iterator[None]:
        """Serialize the entire read/network/write operation across clients/processes.

        Advisory local filesystem locking; network filesystems are unsupported.
        Reentrant in one thread. Timeout produces a safe StorageError.
        """
        if not self._thread_lock.acquire(timeout=5):
            raise StorageError()
        descriptor: int | None = None
        acquired = False
        try:
            if self._depth:
                self._depth += 1
                try:
                    yield
                finally:
                    self._depth -= 1
                return
            path = self.root / ".sdk.lock"
            descriptor = os.open(path, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
            self._chmod(path, 0o600)
            if os.fstat(descriptor).st_size == 0:
                os.write(descriptor, b"0")
            deadline = time.monotonic() + 5
            while not acquired:
                try:
                    self._file_lock(descriptor, True)
                    acquired = True
                except OSError:
                    if time.monotonic() >= deadline:
                        raise StorageError() from None
                    time.sleep(0.02)
            self._depth = 1
            try:
                yield
            finally:
                self._depth = 0
        except OSError:
            raise StorageError() from None
        finally:
            try:
                if descriptor is not None:
                    try:
                        if acquired:
                            self._file_lock(descriptor, False)
                    finally:
                        os.close(descriptor)
            except OSError:
                raise StorageError() from None
            finally:
                self._thread_lock.release()

    @staticmethod
    def _file_lock(descriptor: int, acquire: bool) -> None:
        if os.name == "nt":  # pragma: no cover — native Windows CI required
            msvcrt = importlib.import_module("msvcrt")

            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_NBLCK if acquire else msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB if acquire else fcntl.LOCK_UN)

    def installation_id(self) -> str:
        with self.lock():
            existing = self._read_json(self.identity_path)
            if existing is not None:
                value = existing.get("installation_id")
                if isinstance(value, str) and value.startswith("lmp-install-"):
                    try:
                        uuid.UUID(value[12:])
                        return value
                    except ValueError:
                        pass
                raise StorageError()  # Never silently consume a new seat after corruption.
            value = "lmp-install-" + str(uuid.uuid4())
            self._write_json(self.identity_path, {"installation_id": value})
            return value

    def load_state(self) -> dict[str, Any]:
        return self._read_json(self.state_path) or {}

    def save_state(self, state: dict[str, Any]) -> None:
        self._write_json(self.state_path, state)

    def clear_state(self) -> None:
        self._unlink(self.state_path)

    def load_fallback_token(self) -> str | None:
        raw = self._read(self.token_path)
        if raw is None:
            return None
        try:
            value = raw.decode("utf-8").strip()
            if not value.startswith("act_") or not 8 <= len(value) <= 1024 or any(c.isspace() for c in value):
                raise ValueError()
            return value
        except (UnicodeError, ValueError):
            raise StorageError() from None

    def save_fallback_token(self, token: str) -> None:
        self._atomic_write(self.token_path, token.encode())

    def clear_fallback_token(self) -> None:
        self._unlink(self.token_path)

    def _read(self, path: Path) -> bytes | None:
        descriptor: int | None = None
        try:
            descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or (
                os.name != "nt" and (info.st_uid != os.getuid() or info.st_mode & 0o077)
            ):
                raise StorageError()
            raw = os.read(descriptor, MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise StorageError()
            return raw
        except FileNotFoundError:
            return None
        except OSError:
            raise StorageError() from None
        finally:
            if descriptor is not None:
                os.close(descriptor)

    def _read_json(self, path: Path) -> dict[str, Any] | None:
        raw = self._read(path)
        if raw is None:
            return None
        try:
            value = loads(raw)
            if isinstance(value, dict):
                return value
        except (ValueError, UnicodeError, RecursionError):
            pass
        raise StorageError()

    def _write_json(self, path: Path, value: dict[str, Any]) -> None:
        self._atomic_write(path, canonical(value))

    def _atomic_write(self, path: Path, data: bytes) -> None:
        temporary: Path | None = None
        try:
            descriptor, name = tempfile.mkstemp(prefix=path.name + ".", dir=self.root)
            temporary = Path(name)
            with os.fdopen(descriptor, "wb") as handle:
                self._chmod(temporary, 0o600)
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            self._chmod(path, 0o600)
        except OSError:
            raise StorageError() from None
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    raise StorageError() from None

    @staticmethod
    def _chmod(path: Path, mode: int) -> None:
        if os.name != "nt":
            path.chmod(mode)  # Fail closed; Windows needs a private user ACL.

    @staticmethod
    def _unlink(path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            raise StorageError() from None


class CredentialStore:
    def __init__(
        self, local: LocalStateStore, service: str, username: str, prefer_keyring: bool = True
    ) -> None:
        self.local = local
        self.service = service
        self.username = username
        self._keyring: Any = None
        if prefer_keyring:
            try:
                module = importlib.import_module("keyring")
                if float(module.get_keyring().priority) > 0:
                    self._keyring = module
            except Exception:
                pass

    @property
    def security(self) -> str:
        return "os-keyring" if self._keyring is not None else "permission-protected-file"

    def load(self) -> str | None:
        if self._keyring is not None:
            try:
                value: Any = self._keyring.get_password(self.service, self.username)
                if value is not None:
                    if (
                        not isinstance(value, str)
                        or not value.startswith("act_")
                        or not 8 <= len(value) <= 1024
                        or any(c.isspace() for c in value)
                    ):
                        raise StorageError()
                    return value
            except Exception:
                if self.local.load_fallback_token() is None:
                    raise StorageError() from None
                self._keyring = None
        return self.local.load_fallback_token()

    def save(self, token: str) -> None:
        if self._keyring is not None:
            try:
                self._keyring.set_password(self.service, self.username, token)
            except Exception:
                # Do not switch away from a backend holding an older token.
                try:
                    old = self._keyring.get_password(self.service, self.username)
                except Exception:
                    raise StorageError() from None
                if old:
                    raise StorageError() from None
                self._keyring = None
            else:
                self.local.clear_fallback_token()
                return
        self.local.save_fallback_token(token)

    def clear(self) -> None:
        if self._keyring is not None:
            try:
                existing = self._keyring.get_password(self.service, self.username)
                if existing is not None:
                    self._keyring.delete_password(self.service, self.username)
            except Exception:
                raise StorageError() from None
        self.local.clear_fallback_token()
