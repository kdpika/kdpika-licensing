"""Deprecated import compatibility for the former local source distribution."""

import warnings

from kdpika_licensing import (
    AsyncLicenseClient,
    ConfigurationError,
    LicenseClient,
    LicenseResult,
    LicenseSdkError,
    NetworkError,
    SignatureVerificationError,
    StorageError,
    __version__,
)

warnings.warn("license_sdk is deprecated; import kdpika_licensing instead.", DeprecationWarning, stacklevel=2)
__all__ = [
    "AsyncLicenseClient",
    "ConfigurationError",
    "LicenseClient",
    "LicenseResult",
    "LicenseSdkError",
    "NetworkError",
    "SignatureVerificationError",
    "StorageError",
    "__version__",
]
