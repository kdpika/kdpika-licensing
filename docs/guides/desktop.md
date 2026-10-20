# Desktop and Qt

Install `.[qt]` locally (or the approved registry package's qt extra).
Run `python examples/pyqt_activation.py` in a desktop session with private
KDP_APP_ID/KDP_STATE_DIR configuration. Email matching is a server policy;
email_required in the dialog only enforces a nonempty UI field.

The optional dialog is lazy-loaded and blocks while contacting the service.
Do not treat it as an asynchronous Qt architecture. Target-OS native GUI tests
are still needed; the regression suite uses widget doubles, not real windows.

Keep per-user state outside the application bundle and temporary PyInstaller
extraction directory. Preserve app name/origin/App ID/environment during updates.
The SDK does not ship a tested PyInstaller spec or claim an OS vault is usable
on every machine. See [Storage](../storage.md).
