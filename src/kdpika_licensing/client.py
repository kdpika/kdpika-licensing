"""Synchronous API-v1 installation licensing with authenticated decisions."""

from __future__ import annotations

import hashlib
import platform
import time
import warnings
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ._storage import CredentialStore, LocalStateStore, default_storage_root, storage_namespace
from ._transport import HttpTransport, Transport, safe_url
from ._verification import times, timestamp, trusted_key, verify
from .errors import (
    ConfigurationError,
    NetworkError,
    SignatureVerificationError,
    StorageError,
    safe_request_id,
)
from .models import HttpResponse, LicenseResult

_MESSAGES = {
    "INVALID_LICENSE": "Check your license key, application and customer email.",
    "NOT_ACTIVATED": "Enter your license key to activate this installation.",
    "DEVICE_LIMIT_REACHED": "Release an old installation or contact the software publisher.",
    "ACTIVATION_LIMIT_REACHED": "This key has reached its activation limit. Contact the publisher.",
    "APP_VERSION_NOT_SUPPORTED": "Update the application or contact its publisher.",
    "DEVICE_NOT_AUTHORIZED": "This installation needs a new authorized activation.",
    "LICENSE_PENDING": "This license is not ready yet. Contact the publisher.",
    "INVALID_REQUEST": "Check the application configuration and try again.",
    "PLAN_NOT_FOUND": "The requested license plan is unavailable. Contact the publisher.",
    "MAX_DEVICES_REACHED": "Release an old installation or contact the software publisher.",
    "LICENSE_EXPIRED": "Your license has expired. Contact the software publisher.",
    "LICENSE_REVOKED": "This license is no longer available. Contact the software publisher.",
    "LICENSE_SUSPENDED": "This license is paused. Contact the software publisher.",
    "LICENSE_CANCELLED": "This license has ended. Contact the software publisher.",
    "LICENSE_NOT_ACTIVE": "This license is not active. Contact the software publisher.",
    "INVALID_TOKEN": "Activate this installation again using your license key.",
    "DEVICE_MISMATCH": "This activation belongs to another installation.",
    "RATE_LIMITED": "Please wait before trying this license operation again.",
    "INVALID_RESPONSE": "The license response could not be used. Reconnect or contact support.",
    "SIGNATURE_INVALID": SignatureVerificationError.safe_message,
    "KEY_ROTATION_REQUIRED": "The signing key changed. Update your application's trusted key through its publisher.",
    "NETWORK_ERROR": NetworkError.safe_message,
    "STORAGE_ERROR": StorageError.safe_message,
    "INVALID_SIGNED_TIME": "The license response contains an invalid time. Contact support.",
    "CLOCK_ROLLBACK_DETECTED": "Check your computer's date and time, then reconnect.",
    "OFFLINE_CACHE_INVALID": "Reconnect to refresh this installation's license.",
    "OFFLINE_CACHE_MISSING": "This installation needs an online license check.",
    "OFFLINE_GRACE_EXPIRED": "Connect to the internet to check your license.",
    "HTTP_ERROR": "The licensing service could not complete the request. Contact support.",
}


class LicenseClient:
    """Manage one stable installation and its signed access state.

    Mutating/check operations serialize across clients/processes sharing the
    same local directory. Use a private local filesystem, not NFS. HTTPS is
    required; allow_loopback_http is an explicit local-test-only opt-in.
    The default environment remains LIVE for compatibility; use SANDBOX in tests.

    Args:
        product: Public App ID from the platform, never a developer API key.
        environment: LIVE or SANDBOX; production/test are accepted aliases.
        base_url: HTTPS site origin without a path, credentials or query.
        application_name: Your app name; also determines the default state folder.
        application_version: Your software version sent during activation.
        verification_key: Optional pinned key_id/public_key dictionary. Ed25519
            and base64url only; the ID must match the public-key hash.
        storage_dir: Persistent private root; the SDK adds a product/environment namespace.
        timeout: Default transport socket timeout in seconds, greater than 0 and at most 120.
        prefer_keyring: Try an available optional OS keyring before private files.
        transport: Advanced trusted transport injection; private protocol, no verification bypass.
        clock: Injectable aware datetime provider; normal apps should keep the UTC default.
        allow_loopback_http: Explicit local testing opt-in, never for remote HTTP.

    Attributes:
        product: Normalized configured Public App ID.
        environment: Normalized LIVE or SANDBOX name.
        base_url: Configured API origin.
        application_name: Descriptive app name.
        application_version: Descriptive app version.
        installation_id: Persisted random identity. Preserve it across launches/upgrades.

    Raises:
        ConfigurationError: Invalid origin, environment, product, timeout or pin.
        StorageError: State/identity cannot be initialized safely.

    Examples:
        Create temporary Sandbox state without making a network request:

        >>> from tempfile import TemporaryDirectory
        >>> from pathlib import Path
        >>> with TemporaryDirectory() as directory:
        ...     client = LicenseClient("app_synthetic", environment="SANDBOX",
        ...         storage_dir=Path(directory), prefer_keyring=False)
        ...     print(client.check().error_code)
        NOT_ACTIVATED
    """

    def __init__(
        self,
        product: str,
        environment: str = "production",
        base_url: str = "https://licensing.kdpika.com",
        application_name: str = "Licensed Application",
        application_version: str = "",
        verification_key: dict[str, str] | None = None,
        storage_dir: Path | None = None,
        timeout: float = 15.0,
        prefer_keyring: bool = True,
        transport: Transport | None = None,
        clock: Callable[[], datetime] | None = None,
        *,
        allow_loopback_http: bool = False,
    ) -> None:
        if (
            not isinstance(product, str)
            or not product.strip()
            or not isinstance(environment, str)
            or not safe_url(base_url, allow_loopback_http)
        ):
            raise ConfigurationError()
        normalized = {"PRODUCTION": "LIVE", "TEST": "SANDBOX"}.get(
            environment.strip().upper(), environment.strip().upper()
        )
        if normalized not in {"SANDBOX", "LIVE"}:
            raise ConfigurationError()
        self.product = product.strip()
        self.environment = normalized
        self.base_url = base_url.rstrip("/")
        self.application_name = application_name
        self.application_version = application_version
        try:
            self._pinned_key = trusted_key(verification_key) if verification_key is not None else None
        except SignatureVerificationError:
            raise ConfigurationError() from None
        self._session_key: dict[str, str] | None = None
        self._last_key_fetch: float | None = None
        self._clock = clock or (lambda: datetime.now(UTC))
        self._transport = transport or HttpTransport(
            self.base_url, timeout, allow_loopback_http=allow_loopback_http
        )
        namespace = storage_namespace(self.base_url, self.product, self.environment)
        root = Path(storage_dir) if storage_dir is not None else default_storage_root(application_name)
        self._local = LocalStateStore(root, namespace)
        self.installation_id = self._local.installation_id()
        # Preserve the pre-rename service ID and namespace to avoid orphaning seats.
        service = "com.studiosoline.license-sdk." + hashlib.sha256(namespace.encode("ascii")).hexdigest()[:20]
        self._credentials = CredentialStore(self._local, service, self.installation_id, prefer_keyring)

    @property
    def local(self) -> LocalStateStore:
        """Deprecated internal storage escape hatch; not part of the stable API."""
        warnings.warn("local is internal; configure storage_dir instead.", DeprecationWarning, stacklevel=2)
        return self._local

    @property
    def credentials(self) -> CredentialStore:
        """Deprecated internal credential escape hatch."""
        warnings.warn(
            "credentials is internal; use client lifecycle methods.", DeprecationWarning, stacklevel=2
        )
        return self._credentials

    @property
    def transport(self) -> Transport:
        """Deprecated mutable transport; inject a trusted transport at construction."""
        warnings.warn("transport is internal; inject it at construction.", DeprecationWarning, stacklevel=2)
        return self._transport

    @transport.setter
    def transport(self, value: Transport) -> None:
        warnings.warn(
            "Changing transport is deprecated; inject it at construction.", DeprecationWarning, stacklevel=2
        )
        self._transport = value

    @property
    def storage_security(self) -> str:
        """Report keyring or file storage; this is not an OS security certification."""
        return self._credentials.security

    @property
    def activated(self) -> bool:
        """Whether a token is stored; never use this as an access decision."""
        try:
            with self._local.lock():
                return self._credentials.load() is not None
        except StorageError:
            return False

    def activate(self, license_key: str, email: str | None = None) -> LicenseResult:
        """Activate this persistent installation online.

        Args:
            license_key: Customer key obtained privately, never logged.
            email: Customer email when the product's policy requires a match.

        Returns:
            Signed access decision, or an invalid result with a stable error code.
            HTTP refusals/network/storage failures never grant features.

        Examples:
            See the tested examples/basic.py and examples/session.py scripts.
            Require result.valid and result.signature_valid before protected work.
        """
        return self._run(lambda: self._activate(license_key, email))

    def check(self, force_online: bool = False) -> LicenseResult:
        """Check current access from verified cache or the service.

        Args:
            force_online: Request fresh validation rather than an ordinary cache hit.
                A transport failure can still use authentic unexpired signed grace.

        Returns:
            Current decision. An authoritative HTTP refusal never falls back to cache.
        """
        return self._run(lambda: self._check(force_online))

    def validate(self) -> LicenseResult:
        """Request online validation, equivalent to check(force_online=True).

        Returns:
            Fresh decision, or signed offline-grace decision on a network failure.
                This is not a strict online-only/payment-verification operation.
        """
        return self.check(force_online=True)

    def deactivate(self) -> LicenseResult:
        """Release the server seat before clearing credentials; preserve identity.

        Returns:
            valid=True only for a successful release acknowledgement. It has no
            verified license signature and cannot enable features. Failure keeps
            recovery state where safe; do not blindly retry an uncertain outcome.
        """
        return self._run(self._deactivate)

    def feature(self, name: str, default: bool = False) -> bool:
        """Re-check access and evaluate a boolean/numeric entitlement.

        Args:
            name: Feature key configured in the product's license plan.
            default: Missing-feature fallback only for a valid verified decision.

        Returns:
            False on any refused/unsigned/expired decision, regardless of default.
        """
        return self.check().feature(name, default)

    def feature_value(self, name: str, default: Any = None) -> Any:
        """Re-check access, then read an entitlement without interpreting its type.

        Args:
            name: Configured feature/limit key.
            default: Missing-key fallback only while the decision authorizes access.

        Returns:
            Detached entitlement value, or None on failure. Validate a numeric
            value's type/range before using it as an application limit.
        """
        return self.check().feature_value(name, default)

    def reset_local(self) -> None:
        """Erase token/cache, preserving identity. This does NOT release a seat.

        Raises:
            StorageError: Locking, file cleanup or keyring deletion failed.

        Examples:
            Prefer deactivate() first. Do not delete identity to bypass seat limits.
        """
        with self._local.lock():
            self._local.clear_state()
            self._credentials.clear()

    def _run(self, operation: Callable[[], LicenseResult]) -> LicenseResult:
        try:
            with self._local.lock():
                return operation()
        except StorageError:
            return self._error("STORAGE_ERROR", "local")

    def _activate(self, license_key: str, email: str | None) -> LicenseResult:
        if not isinstance(license_key, str) or not license_key.strip():
            return self._error("INVALID_LICENSE", "local")
        body: dict[str, Any] = {
            "license_key": license_key.strip(),
            "device_id": self.installation_id,
            "device_name": platform.node() or self.application_name,
            "platform": platform.system().lower(),
            "app_version": self.application_version,
        }
        if email:
            body["email"] = email.strip()
        try:
            response = self._transport.request(
                "POST", "/api/v1/licenses/activate", body, self._product_headers()
            )
        except NetworkError:
            return self._error("NETWORK_ERROR", "local")
        if not response.ok:
            return self._response_error(response)
        token, signed = response.body.get("activation_token"), response.body.get("license")
        if (
            not isinstance(token, str)
            or not token.startswith("act_")
            or not 8 <= len(token) <= 1024
            or any(c.isspace() for c in token)
            or not isinstance(signed, dict)
        ):
            return self._error("INVALID_RESPONSE", "online", response)
        result = self._authenticate(signed, "online", response)
        if not result.valid:
            self._revoke_untrusted_activation(token)
            return result
        try:
            self._credentials.save(token)
            self._save_signed_state(signed)
        except StorageError:
            try:
                self._local.clear_state()
            finally:
                self._revoke_untrusted_activation(token)
            raise
        return result

    def _check(self, force_online: bool) -> LicenseResult:
        token = self._credentials.load()
        if not token:
            return self._error("NOT_ACTIVATED", "local")
        state = self._state(recover=True)
        signed = state.get("signed_license")
        if not force_online and isinstance(signed, dict):
            cached = self._authenticate(signed, "cache")
            if cached.valid and self._now() < timestamp(cached.payload.get("next_validation_at")):
                self._checkpoint()
                return cached
        try:
            response = self._transport.request(
                "POST",
                "/api/v1/licenses/validate",
                {},
                {"Authorization": "Bearer " + token, "X-Installation-ID": self.installation_id},
            )
        except NetworkError:
            return self._offline_result()
        if not response.ok:
            result = self._response_error(response)
            self._local.clear_state()
            if result.error_code in {
                "INVALID_TOKEN",
                "DEVICE_MISMATCH",
                "LICENSE_REVOKED",
                "LICENSE_EXPIRED",
                "LICENSE_CANCELLED",
                "LICENSE_SUSPENDED",
            }:
                self._credentials.clear()
            return result
        signed = response.body.get("license")
        if not isinstance(signed, dict):
            self._local.clear_state()
            return self._error("INVALID_RESPONSE", "online", response)
        result = self._authenticate(signed, "online", response)
        if result.valid:
            self._save_signed_state(signed)
        else:
            self._local.clear_state()  # A rejected response cannot leave an old grant behind.
        return result

    def _deactivate(self) -> LicenseResult:
        token = self._credentials.load()
        if not token:
            return self._error("NOT_ACTIVATED", "local")
        try:
            response = self._transport.request(
                "POST", "/api/v1/licenses/deactivate", {}, {"Authorization": "Bearer " + token}
            )
        except NetworkError:
            return self._error("NETWORK_ERROR", "local")
        if not response.ok:
            return self._response_error(response)
        if response.body.get("deactivated") is not True:
            return self._error("INVALID_RESPONSE", "online", response)
        self.reset_local()
        return LicenseResult(
            True,
            "online",
            request_id=self._request_id(response),
            message="License deactivated.",
            storage_security=self.storage_security,
        )

    def _revoke_untrusted_activation(self, token: str) -> None:
        try:
            self._transport.request(
                "POST", "/api/v1/licenses/deactivate", {}, {"Authorization": "Bearer " + token}
            )
        except NetworkError:
            pass  # Uncertain cleanup: retry requires the same persistent identity.

    def _offline_result(self) -> LicenseResult:
        signed = self._state(recover=True).get("signed_license")
        if not isinstance(signed, dict):
            return self._error("OFFLINE_CACHE_MISSING", "offline")
        result = self._authenticate(signed, "offline")
        if result.valid:
            self._checkpoint()
        elif result.error_code == "SIGNATURE_INVALID":
            self._local.clear_state()
            return self._error("OFFLINE_CACHE_INVALID", "offline")
        return result

    def _authenticate(
        self, signed: dict[str, Any], source: str, response: HttpResponse | None = None
    ) -> LicenseResult:
        if self._pinned_key and signed.get("key_id") != self._pinned_key["key_id"]:
            return self._error("KEY_ROTATION_REQUIRED", source, response)
        try:
            payload = verify(signed, self._verification_key(signed, online=source == "online"))
        except (SignatureVerificationError, NetworkError):
            return self._error("SIGNATURE_INVALID", source, response)
        device = payload.get("device")
        if (
            payload.get("product_id") != self.product
            or not isinstance(payload.get("environment"), str)
            or str(payload["environment"]).upper() != self.environment
            or not isinstance(device, dict)
            or device.get("installation_hash") != hashlib.sha256(self.installation_id.encode()).hexdigest()
        ):
            return self._error("SIGNATURE_INVALID", source, response)
        try:
            server, _, grace, expiry = times(payload)
            now = self._now()
            checkpoint_raw = self._state(recover=False).get("last_seen_at")
            checkpoint = timestamp(checkpoint_raw) if checkpoint_raw is not None else server
        except (ValueError, TypeError, OverflowError):
            return self._error("INVALID_SIGNED_TIME", source, response)
        if now.timestamp() + 300 < max(server, checkpoint).timestamp():
            return self._error("CLOCK_ROLLBACK_DETECTED", source, response, payload, True)
        if payload.get("status") != "active":
            return self._error("LICENSE_NOT_ACTIVE", source, response, payload, True)
        if expiry is not None and now >= expiry:
            return self._error("LICENSE_EXPIRED", source, response, payload, True)
        if source in {"cache", "offline"} and now > grace:
            return self._error("OFFLINE_GRACE_EXPIRED", source, response, payload, True)
        return LicenseResult(
            True,
            source,
            payload,
            request_id=self._request_id(response),
            signature_valid=True,
            storage_security=self.storage_security,
            _clock=self._now,
        )

    def _verification_key(self, signed: dict[str, Any], *, online: bool) -> dict[str, Any]:
        if self._pinned_key is not None:
            return self._pinned_key
        target = signed.get("key_id")
        if self._session_key is not None and self._session_key["key_id"] == target:
            return self._session_key
        cached = self._state(recover=True).get("verification_key")
        if isinstance(cached, dict) and cached.get("key_id") == target:
            return trusted_key(cached)
        if not online or (self._last_key_fetch is not None and time.monotonic() - self._last_key_fetch < 10):
            raise SignatureVerificationError()
        self._last_key_fetch = time.monotonic()
        response = self._transport.request("GET", "/api/v1/public-key", None, {})
        key = response.body.get("key") if response.ok else None
        if (
            not isinstance(key, dict)
            or key.get("algorithm") != "Ed25519"
            or key.get("encoding") != "base64url"
        ):
            raise SignatureVerificationError()
        validated = trusted_key(key)
        if validated["key_id"] != target:
            raise SignatureVerificationError()
        self._session_key = validated
        return validated

    def _state(self, *, recover: bool) -> dict[str, Any]:
        try:
            return self._local.load_state()
        except StorageError:
            if not recover:
                raise
            self._local.clear_state()
            return {}

    def _save_signed_state(self, signed: dict[str, Any]) -> None:
        state = self._state(recover=True)
        key = self._pinned_key or self._session_key or state.get("verification_key")
        if not isinstance(key, dict) or key.get("key_id") != signed.get("key_id"):
            key = self._verification_key(signed, online=True)
        state.update(version=1, signed_license=signed, verification_key=key)
        state["last_seen_at"] = max(self._now(), timestamp(signed["payload"]["server_time"])).isoformat()
        self._local.save_state(state)

    def _checkpoint(self) -> None:
        state = self._state(recover=False)
        previous = timestamp(state["last_seen_at"])
        state["last_seen_at"] = max(previous, self._now()).isoformat()
        self._local.save_state(state)

    def _response_error(self, response: HttpResponse) -> LicenseResult:
        error = response.body.get("error")
        code = error.get("code") if isinstance(error, dict) else None
        code = code if isinstance(code, str) and code in _MESSAGES else "HTTP_ERROR"
        return self._error(code, "online", response)

    def _error(
        self,
        code: str,
        source: str,
        response: HttpResponse | None = None,
        payload: dict[str, Any] | None = None,
        signature_valid: bool = False,
    ) -> LicenseResult:
        return LicenseResult(
            False,
            source,
            payload or {},
            code,
            _MESSAGES[code],
            self._request_id(response),
            signature_valid,
            self.storage_security,
            self._now,
        )

    def _product_headers(self) -> dict[str, str]:
        return {"X-App-ID": self.product, "X-Environment": self.environment}

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None:
            raise ValueError("An aware UTC clock is required")
        return value.astimezone(UTC)

    @staticmethod
    def _request_id(response: HttpResponse | None) -> str | None:
        return safe_request_id(response.body.get("request_id")) if response else None
