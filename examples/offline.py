"""Refresh online; only the SDK may fall back to authentic unexpired signed grace."""

import json

from _common import configured_client, ensure_activation, run, summary


def main() -> int:
    client = configured_client()
    initial = ensure_activation(client)
    if not initial.valid or not initial.signature_valid:
        print(json.dumps(summary(initial)))
        return 1
    result = client.validate()
    print(json.dumps({**summary(result), "signed_offline_decision": result.source == "offline"}))
    return 0 if result.valid and result.signature_valid else 1


if __name__ == "__main__":
    run(main)
