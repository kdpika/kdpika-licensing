"""Strict envelope, signing-key and signed-time validation."""

from __future__ import annotations

import base64
import hashlib
import re
from datetime import UTC, datetime
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from ._json import canonical
from .errors import SignatureVerificationError


def decode(value: Any, size: int) -> bytes:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise SignatureVerificationError()
    try:
        raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except ValueError:
        raise SignatureVerificationError() from None
    if len(raw) != size or base64.urlsafe_b64encode(raw).decode().rstrip("=") != value:
        raise SignatureVerificationError()
    return raw


def trusted_key(key: dict[str, Any]) -> dict[str, str]:
    raw = decode(key.get("public_key"), 32)
    identity = "ed25519_" + hashlib.sha256(raw).hexdigest()[:16]
    if (
        key.get("key_id") != identity
        or key.get("algorithm", "Ed25519") != "Ed25519"
        or key.get("encoding", "base64url") != "base64url"
    ):
        raise SignatureVerificationError()
    return {
        "key_id": identity,
        "public_key": str(key["public_key"]),
        "algorithm": "Ed25519",
        "encoding": "base64url",
    }


def verify(signed: dict[str, Any], key: dict[str, Any]) -> dict[str, Any]:
    """Authenticate bytes only; license policy must be checked separately."""
    key = trusted_key(key)
    payload = signed.get("payload")
    if (
        not isinstance(payload, dict)
        or signed.get("algorithm") != "Ed25519"
        or signed.get("key_id") != key["key_id"]
    ):
        raise SignatureVerificationError()
    try:
        Ed25519PublicKey.from_public_bytes(decode(key["public_key"], 32)).verify(
            decode(signed.get("signature"), 64), canonical(payload)
        )
    except (ValueError, TypeError, InvalidSignature, RecursionError, UnicodeError):
        raise SignatureVerificationError() from None
    return payload


def timestamp(value: Any) -> datetime:
    """Require an unambiguous offset-aware ISO timestamp; never infer lifetime."""
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})", value
    ):
        raise ValueError("Invalid signed time")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(UTC)


def times(payload: dict[str, Any]) -> tuple[datetime, datetime, datetime, datetime | None]:
    server = timestamp(payload.get("server_time"))
    next_check = timestamp(payload.get("next_validation_at"))
    grace = timestamp(payload.get("offline_grace_until"))
    if "expires_at" not in payload:
        raise ValueError("Missing expiry")
    expiry = None if payload["expires_at"] is None else timestamp(payload["expires_at"])
    if next_check < server or grace < server:
        raise ValueError("Invalid signed time order")
    return server, next_check, grace, expiry
