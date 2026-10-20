# Generated public API

Generated from the installed source docstrings, not a second API implementation.
Use [Configuration](configuration.md) and the tested source examples for setup.

::: kdpika_licensing.LicenseClient
    options:
      members: [__init__, activated, storage_security, activate, check, validate, deactivate, feature, feature_value, reset_local]

::: kdpika_licensing.LicenseResult
    options:
      members: [status, license_id, expires_at, offline_grace_until, features, feature, feature_value]

::: kdpika_licensing.AsyncLicenseClient
    options:
      members: [__init__, storage_security, is_activated, activate, check, validate, deactivate, feature, feature_value, reset_local]

::: kdpika_licensing.LicenseSdkError

::: kdpika_licensing.ConfigurationError

::: kdpika_licensing.NetworkError

::: kdpika_licensing.SignatureVerificationError

::: kdpika_licensing.StorageError

::: kdpika_licensing.ui.show_activation_dialog

Private modules and deprecated local/credentials/transport escape hatches are
not stable extension APIs. Only an advanced trusted custom transport should
use the private protocol; it must decode signed data losslessly.
