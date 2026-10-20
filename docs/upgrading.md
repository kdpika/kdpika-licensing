# Upgrading and uninstalling

Use a private test environment first. After official publication, select/pin
the intended version explicitly (pre-releases require an explicit version or
--pre). Keep app name/origin/App ID/environment and persistent state directory.

Validate activation, restart, offline grace and deactivation in Sandbox before
rolling out a new build. Review the changelog and key-pin rotation policy.
Backups contain private credentials and must never be sent to public support.

Before uninstalling, confirm successful deactivate to release the seat.
Then uninstall with pip. reset_local, deleting a folder, or pip uninstall alone
does not release a server seat. Do not blindly retry uncertain HTTP mutations.
