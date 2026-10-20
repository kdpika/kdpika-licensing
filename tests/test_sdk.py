import base64
import hashlib
import json
import os
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from license_sdk import ConfigurationError, LicenseClient, NetworkError
from license_sdk.models import HttpResponse


class FakeTransport:
    def __init__(self, now):
        self.private = Ed25519PrivateKey.generate()
        self.key_id = (
            "ed25519_" + hashlib.sha256(self.private.public_key().public_bytes_raw()).hexdigest()[:16]
        )
        self.now = now
        self.mode = "online"
        self.calls = []

    def request(self, method, path, body=None, headers=None):
        self.calls.append((method, path, body, headers))
        if path == "/api/v1/public-key":
            return HttpResponse(
                200,
                {},
                {
                    "success": True,
                    "key": {
                        "algorithm": "Ed25519",
                        "encoding": "base64url",
                        "key_id": self.key_id,
                        "public_key": self._encode(self.private.public_key().public_bytes_raw()),
                    },
                },
            )
        if path == "/api/v1/licenses/activate":
            return HttpResponse(
                200,
                {},
                {
                    "success": True,
                    "activation_token": "act_test_secret_token",
                    "license": self.signed(body["device_id"]),
                    "request_id": "req_activate",
                },
            )
        if path == "/api/v1/licenses/validate":
            if self.mode == "network":
                raise NetworkError("offline")
            if self.mode == "revoked":
                return HttpResponse(
                    403,
                    {},
                    {
                        "success": False,
                        "error": {"code": "LICENSE_REVOKED", "message": "This license is not active."},
                        "request_id": "req_revoked",
                    },
                )
            device_id = self._device_from_authorization(headers)
            return HttpResponse(
                200,
                {},
                {
                    "success": True,
                    "valid": True,
                    "license": self.signed(device_id),
                    "request_id": "req_validate",
                },
            )
        if path == "/api/v1/licenses/deactivate":
            return HttpResponse(
                200, {}, {"success": True, "deactivated": True, "request_id": "req_deactivate"}
            )
        raise AssertionError("Unexpected request: " + path)

    def signed(self, device_id, **changes):
        now = self.now[0]
        payload = {
            "license_id": "lic_test",
            "product_id": "app_test",
            "product": "Test Product",
            "plan": "pro",
            "status": "active",
            "environment": "sandbox",
            "expires_at": (now + timedelta(days=30)).isoformat(),
            "features": {"pdf_export": True, "seat_count": 5},
            "device": {
                "id": "dev_test",
                "installation_hash": hashlib.sha256(device_id.encode()).hexdigest(),
                "name": "Test",
                "platform": "test",
                "app_version": "1.0",
            },
            "server_time": now.isoformat(),
            "next_validation_at": (now + timedelta(hours=24)).isoformat(),
            "offline_grace_until": (now + timedelta(days=7)).isoformat(),
        }
        payload.update(changes)
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        return {
            "payload": payload,
            "signature": self._encode(self.private.sign(canonical)),
            "algorithm": "Ed25519",
            "key_id": self.key_id,
        }

    def _device_from_authorization(self, headers):
        # The token is installation-scoped on the real server. Tests derive the
        # device from the most recent activation request without exposing it.
        for _, path, body, _ in reversed(self.calls):
            if path == "/api/v1/licenses/activate":
                return body["device_id"]
        raise AssertionError("No activated device")

    @staticmethod
    def _encode(value):
        return base64.urlsafe_b64encode(value).decode().rstrip("=")


class LicenseClientTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.now = [datetime(2026, 10, 8, 12, 0, tzinfo=UTC)]
        self.transport = FakeTransport(self.now)
        self.client = LicenseClient(
            product="app_test",
            environment="sandbox",
            base_url="https://licenses.example.test",
            application_name="SDK Test",
            storage_dir=Path(self.temp.name),
            prefer_keyring=False,
            transport=self.transport,
            clock=lambda: self.now[0],
        )

    def tearDown(self):
        self.temp.cleanup()

    def activate(self):
        result = self.client.activate("TEST-AAAA-BBBB-CCCC-DDDD", "customer@example.test")
        self.assertTrue(result.valid)
        return result

    def test_activation_verifies_signature_persists_random_identity_and_features(self):
        result = self.activate()
        self.assertEqual("online", result.source)
        self.assertTrue(result.feature("pdf_export"))
        self.assertEqual(5, result.feature_value("seat_count"))
        self.assertTrue(self.client.installation_id.startswith("lmp-install-"))
        second = LicenseClient(
            "app_test",
            "sandbox",
            "https://licenses.example.test",
            "SDK Test",
            storage_dir=Path(self.temp.name),
            prefer_keyring=False,
            transport=self.transport,
            clock=lambda: self.now[0],
        )
        self.assertEqual(self.client.installation_id, second.installation_id)
        self.assertEqual("permission-protected-file", self.client.storage_security)
        token_path = self.client.local.token_path
        self.assertEqual(0o600, os.stat(token_path).st_mode & 0o777)

    def test_cache_avoids_unnecessary_online_validation(self):
        self.activate()
        before = len(self.transport.calls)
        result = self.client.check()
        self.assertTrue(result.valid)
        self.assertEqual("cache", result.source)
        self.assertEqual(before, len(self.transport.calls))

    def test_network_failure_uses_verified_cache_only_inside_grace(self):
        self.activate()
        self.now[0] += timedelta(hours=25)
        self.transport.mode = "network"
        result = self.client.check()
        self.assertTrue(result.valid)
        self.assertEqual("offline", result.source)
        self.now[0] += timedelta(days=7)
        result = self.client.check(force_online=True)
        self.assertFalse(result.valid)
        self.assertEqual("OFFLINE_GRACE_EXPIRED", result.error_code)

    def test_authoritative_revocation_never_falls_back_offline(self):
        self.activate()
        self.now[0] += timedelta(hours=25)
        self.transport.mode = "revoked"
        result = self.client.check()
        self.assertFalse(result.valid)
        self.assertEqual("LICENSE_REVOKED", result.error_code)
        self.assertFalse(self.client.activated)
        self.assertEqual({}, self.client.local.load_state())

    def test_tampered_cached_payload_is_rejected(self):
        self.activate()
        state = self.client.local.load_state()
        state["signed_license"]["payload"]["features"]["pdf_export"] = False
        self.client.local.save_state(state)
        self.transport.mode = "network"
        result = self.client.check(force_online=True)
        self.assertFalse(result.valid)
        self.assertEqual("OFFLINE_CACHE_INVALID", result.error_code)

    def test_clock_rollback_is_detected(self):
        self.activate()
        self.now[0] -= timedelta(hours=1)
        result = self.client.check()
        self.assertFalse(result.valid)
        self.assertEqual("CLOCK_ROLLBACK_DETECTED", result.error_code)

    def test_deactivation_clears_token_and_cache(self):
        self.activate()
        result = self.client.deactivate()
        self.assertTrue(result.valid)
        self.assertFalse(self.client.activated)
        self.assertEqual({}, self.client.local.load_state())

    def test_wrong_pinned_key_rejects_server_payload(self):
        other = Ed25519PrivateKey.generate().public_key().public_bytes_raw()
        with self.assertRaises(ConfigurationError):
            LicenseClient(
                "app_test",
                "sandbox",
                "https://licenses.example.test",
                "Pinned Test",
                verification_key={
                    "key_id": self.transport.key_id,
                    "public_key": FakeTransport._encode(other),
                },
                storage_dir=Path(self.temp.name) / "pinned",
                prefer_keyring=False,
                transport=self.transport,
                clock=lambda: self.now[0],
            )
        self.assertEqual([], self.transport.calls)


if __name__ == "__main__":
    unittest.main()
