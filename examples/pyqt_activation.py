"""Run with the qt extra in a real desktop session; the dialog operation blocks."""

from _common import configured_client, emit, run

from kdpika_licensing.ui import show_activation_dialog


def main() -> int:
    client = configured_client()
    result = client.check()
    if not result.valid or not result.signature_valid:
        result = show_activation_dialog(client, email_required=True)
    # Protected work must check again rather than retaining a permanent grant.
    return emit(result) if result.valid and result.signature_valid else 1


if __name__ == "__main__":
    run(main)
