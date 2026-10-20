# Client configuration

## Configuration reference

LicenseClient accepts these constructor options; no developer API key is needed.

| Option | Type / default | Meaning |
|---|---|---|
| product | str, required | Public App ID |
| environment | str, "production" | LIVE default; SANDBOX for testing; TEST/PRODUCTION aliases |
| base_url | str, https://licensing.kdpika.com | HTTPS origin only, no path/query/user info |
| application_name | str, "Licensed Application" | App label and default state-path component |
| application_version | str, "" | Your app version sent on activation |
| verification_key | dict[str,str] or None | Optional authorized key_id/public_key pin; Ed25519/base64url |
| storage_dir | pathlib.Path or None | Private persistent root; SDK adds namespace |
| timeout | float, 15.0 | Per-request socket timeout, >0 and <=120; not a total wall-time guarantee |
| prefer_keyring | bool, True | Try optional usable native keyring |
| transport | private Transport or None | Advanced trusted injection; preserve wire JSON with HttpResponse.from_bytes |
| clock | callable returning aware datetime or None | UTC clock by default; injection for tests |
| allow_loopback_http | bool, False | Keyword-only explicit local HTTP testing, never remote HTTP |

Pins never rotate automatically. Ordinary clients fetch the current key only
from their configured authenticated HTTPS origin. No envelope-supplied key is trusted.
