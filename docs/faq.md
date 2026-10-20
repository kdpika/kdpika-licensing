# FAQ

## Frequently asked questions

### 1. Is this candidate already on PyPI?
No. Version 1.1.0rc1 is prepared locally. Registry commands below are instructions
for the owner-approved release, not evidence that an upload occurred.

### 2. Which Python versions are supported?
The candidate requires Python 3.11–3.14. Those four interpreters were executed
on arm64 macOS; other operating systems require the configured CI to pass.

### 3. What is the difference between an App ID and a license key?
The public App ID identifies software. A customer's key activates its purchase.
Developer management API keys belong on trusted servers, never distributed apps.

### 4. How do I choose Sandbox?
Pass environment="SANDBOX". TEST is an alias. The default remains LIVE for
backward compatibility. All shipped lifecycle examples explicitly use Sandbox.

### 5. Can a Sandbox license activate in Live?
No. Environment binding is checked. Use a key issued for the selected environment.

### 6. Why is activation refused with an email?
The product's server-side policy may require an exact customer-email match.
Use the purchaser's email or contact the software publisher.

### 7. Does activated=True mean access is valid?
No. It only means an activation token is present. Use a fresh check and require
valid and signature_valid, then inspect required entitlements.

### 8. Why is SIGNATURE_INVALID shown?
The response could not be authenticated or has wrong bindings/encoding.
Check configuration, origin and supported SDK version; never disable verification.

### 9. What does KEY_ROTATION_REQUIRED mean?
Your pinned key differs from the response key. Obtain an authorized app update
from its publisher. The SDK never silently replaces a pin.

### 10. Does the SDK support historical signing keys?
The server currently publishes only its current key. Cached known keys can
verify their own signed state; the SDK cannot invent a historical key ring.

### 11. What if all device seats are used?
Release an old installation through an authorized workflow or contact the
publisher. Deleting local identity is not a legitimate way around seat limits.

### 12. Do upgrades create a new installation?
Not if you preserve app name, origin, App ID, environment and the private state
directory. The namespace, filenames and keyring service remain compatible.

### 13. What if state disappears after packaging or an update?
Check whether your app changed its storage path/name or runs as a different user.
Do not write persistent state inside a temporary PyInstaller extraction folder.

### 14. What happens if identity is corrupt?
Initialization raises StorageError instead of silently consuming a new seat.
Restore a trusted backup or ask the publisher for an authorized recovery.

### 15. Can the app work offline?
Only after activation with an authenticated cached license inside signed expiry
and grace. Grace is an absolute signed deadline, not a fresh timer after failure.

### 16. Does validate() guarantee an online answer?
No. It requests online validation but permits signed offline grace on a network
failure. Inspect source if your own policy requires an online-only operation.

### 17. Will server rejection fall back to old access?
No. An authoritative HTTP refusal or rejected signature does not permit a
network-error fallback to old authorization.

### 18. What if my clock is wrong?
Restore correct automatic date/time and reconnect. Missing/malformed signed
times fail closed; rollback tolerance is 300 seconds, not indefinite access.

### 19. Are private files encrypted?
No. Permission-protected fallback is not encryption or a native vault. Install
the optional keyring extra for a usable OS vault; Windows requires private ACLs.

### 20. Will keyring work on headless Linux?
Not necessarily. A usable backend/session must exist. Check storage_security;
the SDK reports its selected backend and uses a documented fallback where safe.

### 21. Are Windows, Intel macOS and PyInstaller tested?
Only arm64 macOS runtime execution is recorded so far. Native Windows/Linux,
Qt/keyring and PyInstaller acceptance are not certified by the macOS matrix.
cryptography 49+ no longer supplies Intel macOS or 32-bit Windows wheels.

### 22. Can I disable TLS or signatures to work around a firewall?
No. Configure your trusted system CA/proxy correctly. Only explicit loopback
HTTP testing is allowed; never install a TLS/signature bypass in customer apps.

### 23. Are retries automatic?
Only the public-key GET can retry once with bounded jitter/Retry-After handling.
Activation, validation and deactivation POSTs are not automatically replayed.

### 24. What should I do after a timeout or cancellation?
Keep the same installation identity and reconcile the outcome. Cancellation of
an async await does not stop its worker's HTTP request. Do not blindly reactivate.

### 25. How should I handle RATE_LIMITED?
Pause and show a polite retry-later message. The SDK does not run an endless
retry loop or grant old access after an authoritative refusal.

### 26. Can multiple threads/processes share a client state?
Local operations serialize with bounded advisory locks. A busy lock can fail
after five seconds. Do not use NFS, shared users' directories or untrusted paths.

### 27. How do I uninstall safely?
Confirm successful deactivation first, then uninstall the distribution. Removing
local files or pip uninstall alone does not release the server-side seat.

### 28. May I keep a successful result forever?
No. Check before protected work. Helpers re-evaluate signed deadlines, but
result.valid records the original check-time decision, not a permanent grant.

### 29. Why does a numeric feature limit return None?
The decision may be invalid or the key absent. Validate the value's type/range;
do not interpret None, strings or booleans as an unlimited numeric allowance.

### 30. Does the base install require PyQt or a keyring?
No. cryptography is the only direct runtime dependency. qt/keyring are optional;
Flask is required only for the backend example/tests, not by the runtime SDK.

### 31. How do I upgrade from license_sdk?
Remove the old distribution before installing the candidate, update imports to
kdpika_licensing and preserve state. The old import warns but still works.

### 32. What can I safely log or send to support?
Use request_id and a non-sensitive description. Do not send keys, activation
tokens, full payloads, state files, customer emails or raw exception chains.

### 33. Can local licensing stop the machine owner patching my app?
No local SDK can provide that guarantee. Enforce valuable server-side operations
on your authenticated backend too. Do not market the SDK as tamper-proof.

### 34. Is the SDK open source or freely redistributable?
Yes. The SDK and included documentation use the MIT License. Integration and
redistribution in commercial apps are permitted under that license, including
its copyright and permission notice. The separate SaaS platform/backend and
service access are not part of this distribution.

### 35. Where do I report a security problem?
Privately email hi@kdpika.com without secrets. Do not post a live exploit or
customer credentials in a public issue. No guaranteed response SLA is claimed.
