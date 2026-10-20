"""Small public-API fail-closed demonstration; no network or private internals."""

from kdpika_licensing import LicenseResult


def main() -> int:
    result = LicenseResult(False, "local", error_code="NOT_ACTIVATED")
    assert not result.feature("pdf_export", True)
    assert result.feature_value("seat_count", 100) is None
    assert result.features == {}
    print("Unverified data cannot enable an SDK feature helper.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
