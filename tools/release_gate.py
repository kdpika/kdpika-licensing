"""Validate owner decisions and tag/version identity. Never publishes."""

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path

from packaging.version import InvalidVersion, Version

ROOT = Path(__file__).resolve().parents[1]


def version(root: Path = ROOT) -> Version:
    tree = ast.parse((root / "src/kdpika_licensing/_version.py").read_text(encoding="utf-8"))
    value = next(
        ast.literal_eval(n.value)
        for n in tree.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "__version__" for t in n.targets)
    )
    return Version(value)


def validate(config: dict, tag: str, repository: str, root: Path = ROOT) -> Version:
    for key in ["name_approved", "version_approved", "license_approved", "support_email_approved"]:
        if config.get(key) is not True:
            raise ValueError("TODO(owner decision): " + key)
    if config.get("package") != "kdpika-licensing":
        raise ValueError("Distribution name does not match the prepared release")
    declared = config.get("repository", "")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", declared) or declared != repository:
        raise ValueError("TODO(owner decision): confirm the exact GitHub owner/repository")
    if not config.get("support_email") or "@" not in config["support_email"]:
        raise ValueError("Confirm the public support email")
    current = version(root)
    if tag != "v" + str(current) or current.is_devrelease or current.local is not None:
        raise ValueError("Tag must exactly match the non-dev, non-local source version")
    license_bytes = (root / "LICENSE").read_bytes()
    license_hash = hashlib.sha256(license_bytes).hexdigest()
    if (
        not license_bytes.strip()
        or license_hash != config.get("approved_license_sha256")
        or license_hash == "7f3d8a4a04c22e68c286c2cccf8cf31df98891afabc56efc47952ab9a0455658"
    ):
        raise ValueError("Owner-approved LICENSE must be present")
    return current


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--repository", required=True)
    args = parser.parse_args()
    try:
        current = validate(
            json.loads((ROOT / "release-config.json").read_text(encoding="utf-8")), args.tag, args.repository
        )
    except (ValueError, InvalidVersion):
        print("Release blocked: review release-config.json owner decisions and exact tag/repository.")
        return 1
    print(json.dumps({"version": str(current), "prerelease": current.is_prerelease, "owner_gate": "passed"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
