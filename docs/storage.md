# Storage

| OS | Default root before product/environment namespace |
|---|---|
| macOS | ~/Library/Application Support/<app-name>/License |
| Windows | %APPDATA%/<app-name>/License, or home fallback |
| Linux/other | $XDG_DATA_HOME/<app-name>/license, default ~/.local/share |

Configure storage_dir for an explicit persistent private root. Namespace,
installation.json, signed-state.json, activation-token, state version 1 and
the old keyring service ID remain compatible. The .sdk.lock file is new.
Identity survives reset_local/deactivate; deleting it is not a seat-limit fix.

POSIX files/directories are owner-private 0600/0700. Writes use temporary files,
fsync and replace; errors fail safely. Corrupted identity stops rather than
silently creating another seat. Corrupted cache requires online recovery.
Old caches already missing signed number bytes cannot be repaired offline.

Optional usable keyring is preferred; check storage_security. Headless Linux
might have no usable backend. Fallback is permission-protected, not encrypted.
Windows requires user-private ACLs; POSIX symlink/permission tests do not certify
Windows reparse-point protection. Use trusted local storage only.

Thread/process operations serialize with bounded advisory locks. Network
filesystems and cross-user sharing are unsupported. Preserve paths/config
during upgrades and test restore/recovery with disposable Sandbox data.
