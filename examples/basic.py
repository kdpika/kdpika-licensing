"""Minimal activation. Run: python examples/basic.py (Sandbox only)."""

from _common import configured_client, emit, ensure_activation, run


def main() -> int:
    result = ensure_activation(configured_client())
    return emit(result)


if __name__ == "__main__":
    run(main)
