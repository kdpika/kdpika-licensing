# Offline access and clock

A fresh verified online decision can be cached. check uses cache while its
signed next_validation_at is in the future and signed grace/expiry still permit
it. validate requests online; a transport/network failure alone can fall back
to previously authenticated signed state.

No cache means no offline access. Authoritative HTTP refusals, wrong bindings,
bad signatures, expired/suspended/revoked licenses and expired grace deny access.
Grace is the signed absolute offline_grace_until, not a new interval started
after disconnect. Zero grace permits fresh online use, not later cached use.

Signed server_time, next_validation_at, offline_grace_until and expires_at
must be present and well-formed. Lifetime is explicit null expiry. Naive/malformed
times cannot silently become lifetime. Rollback tolerance is 300 seconds and
stored last-seen checkpoints do not move backwards. Restore automatic date/time
and reconnect on clock failures; do not bypass this policy.

Result.valid records the check-time decision. Check before protected work,
require signature_valid, then use helpers which re-evaluate deadlines.
This does not protect against a machine owner replacing all local state/clock.
