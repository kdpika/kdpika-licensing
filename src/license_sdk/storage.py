"""Deprecated compatibility re-export; use the documented public package."""

from kdpika_licensing._storage import (
    CredentialStore,
    LocalStateStore,
    default_storage_root,
    storage_namespace,
)

__all__ = ["CredentialStore", "LocalStateStore", "default_storage_root", "storage_namespace"]
