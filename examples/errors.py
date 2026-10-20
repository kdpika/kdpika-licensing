"""Display SDK-owned messages; log only safe request IDs, never payloads."""

from _common import configured_client, ensure_activation, run

from kdpika_licensing import LicenseResult


def explain(result: LicenseResult) -> str:
    if result.valid and result.signature_valid:
        return "Your license is ready."
    if result.error_code == "RATE_LIMITED":
        return "Please wait before trying again."
    if result.error_code in {"DEVICE_LIMIT_REACHED", "ACTIVATION_LIMIT_REACHED"}:
        return "Release an old installation or contact the software publisher."
    return "Access is unavailable. Check your key, connection and date, or contact the software publisher."


def main() -> int:
    result = ensure_activation(configured_client())
    print(explain(result))
    if result.request_id:
        print("Support request:", result.request_id)
    return 0 if result.valid and result.signature_valid else 1


if __name__ == "__main__":
    run(main)
