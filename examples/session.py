"""Persistent Sandbox CLI; no credentials accepted in command-line arguments."""

import argparse
import json

from _common import activate, configured_client, emit, run


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=["status", "activate", "check", "validate", "deactivate", "clear-local"]
    )
    args = parser.parse_args(argv)
    client = configured_client()
    if args.action == "status":
        print(json.dumps({"activated": client.activated, "storage_security": client.storage_security}))
        return 0
    if args.action == "clear-local":
        client.reset_local()
        print("Local credentials cleared. The server seat was NOT released; identity preserved.")
        return 0
    result = activate(client) if args.action == "activate" else getattr(client, args.action)()
    return emit(result)


if __name__ == "__main__":
    run(main)
