# Errors and safe recovery

## Error codes and recovery

SDK-owned messages are safe to display. Log only the bounded request_id; never
print response payloads, tokens, keys or exception chains.

| Code(s) | Meaning / safe action |
|---|---|
| NOT_ACTIVATED | Ask for a customer key through a private prompt |
| INVALID_LICENSE | Check key, App ID and required customer email |
| DEVICE_LIMIT_REACHED, ACTIVATION_LIMIT_REACHED | Release an authorized old seat or contact publisher |
| MAX_DEVICES_REACHED | Legacy compatibility code; same safe seat-limit action |
| APP_VERSION_NOT_SUPPORTED | Update the app or contact publisher |
| DEVICE_NOT_AUTHORIZED, DEVICE_MISMATCH | Reconcile this installation's authorization |
| INVALID_TOKEN | Activate this same installation again through an authorized flow |
| LICENSE_PENDING | Purchase/license not ready; contact publisher |
| LICENSE_EXPIRED, LICENSE_REVOKED, LICENSE_SUSPENDED, LICENSE_CANCELLED, LICENSE_NOT_ACTIVE | No access; show a plain renewal/support message |
| INVALID_REQUEST, PLAN_NOT_FOUND | Check integration/product configuration |
| RATE_LIMITED | Wait; no busy retry loop |
| NETWORK_ERROR | No authoritative response; only authentic signed grace may permit access |
| INVALID_RESPONSE, HTTP_ERROR | Response cannot authorize access; reconnect/contact publisher |
| SIGNATURE_INVALID | Authentication/binding failed; never bypass verification |
| KEY_ROTATION_REQUIRED | Publisher-controlled update of a configured pin required |
| INVALID_SIGNED_TIME, CLOCK_ROLLBACK_DETECTED | Correct date/time, reconnect or contact publisher |
| OFFLINE_CACHE_INVALID, OFFLINE_CACHE_MISSING, OFFLINE_GRACE_EXPIRED | Connect to refresh authorization |
| STORAGE_ERROR | Fix private storage permissions/keyring; do not delete identity to bypass limits |
| ACTIVATION_CANCELLED | Optional Qt dialog cancelled; not an access grant |

ConfigurationError may be raised during initialization, StorageError during
identity/storage setup or explicit reset_local. Most lifecycle/network refusals
return LicenseResult instead. Exceptions share LicenseSdkError; safe code and
request_id are available. Constructed application messages are not verified data.
