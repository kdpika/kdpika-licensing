"""Deprecated compatibility re-export; use the documented public package."""

from kdpika_licensing.errors import (
    ConfigurationError,
    LicenseSdkError,
    NetworkError,
    SignatureVerificationError,
    StorageError,
)

__all__ = [
    "LicenseSdkError",
    "ConfigurationError",
    "NetworkError",
    "SignatureVerificationError",
    "StorageError",
]
