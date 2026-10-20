"""Gate an example feature and a numeric limit without trusting a failed result."""

import json

from _common import configured_client, ensure_activation, run

from kdpika_licensing import LicenseResult


def permissions(result: LicenseResult) -> dict[str, object]:
    verified = result.valid and result.signature_valid
    value = result.feature_value("seat_count") if verified else None
    limit = value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None
    return {"pdf_export": bool(verified and result.feature("pdf_export")), "seat_count": limit}


def main() -> int:
    result = ensure_activation(configured_client())
    print(json.dumps(permissions(result)))
    return 0 if result.valid and result.signature_valid else 1


if __name__ == "__main__":
    run(main)
