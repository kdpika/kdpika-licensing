"""Audit actual fresh base installation from verify_artifacts.py; no publishing."""

import argparse
import json
import subprocess
import sys
import sysconfig
from importlib.metadata import distributions
from pathlib import Path
from tempfile import TemporaryDirectory

from packaging.utils import canonicalize_name
from packaging.version import Version

ROOT = Path(__file__).resolve().parents[1]


def audit(site: str, output: Path) -> int:
    """Audit every installed third-party distribution, not our unpublished candidate."""
    requirements = set()
    candidate = []
    for dist in distributions(path=[site]):
        name = canonicalize_name(dist.metadata["Name"], validate=True)
        version = str(Version(dist.version))
        if name == "kdpika-licensing":
            candidate.append({"name": name, "version": version})
        else:
            requirements.add(f"{name}=={version}")
    if not requirements:
        raise ValueError("No installed third-party distributions found to audit")
    # This is the complete installed inventory, including transitive dependencies.
    # Do not resolve again or replace the versions in the verified installation.
    with TemporaryDirectory(prefix="kdpika-audit-") as temp:
        pinned = Path(temp) / "requirements.txt"
        pinned.write_text("\n".join(sorted(requirements)) + "\n", encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip_audit",
                "--requirement",
                str(pinned),
                "--no-deps",
                "--disable-pip",
                "--strict",
                "--progress-spinner",
                "off",
                "--format",
                "json",
                "--output",
                str(output),
            ],
            check=False,
        )
    if output.exists():
        report = json.loads(output.read_text(encoding="utf-8"))
        report["audit_scope"] = {
            "installed_third_party_requirements": sorted(requirements),
            "excluded_own_candidate": candidate,
            "reason": "Own candidate is source/artifact-tested, not a published dependency",
        }
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tooling", action="store_true", help="Audit the current dedicated tools environment"
    )
    args = parser.parse_args()
    if args.tooling:
        site = sysconfig.get_paths()["purelib"]
        output = "dependency-audit-tooling-release.json"
    else:
        report = json.loads(
            (ROOT / "docs/internal/artifact-verification-release.json").read_text(encoding="utf-8")
        )
        python = report["artifacts"]["wheel"]["python"]
        site = subprocess.check_output(
            [python, "-c", "import sysconfig;print(sysconfig.get_paths()['purelib'])"], text=True
        ).strip()
        output = "dependency-audit-release.json"
    (ROOT / "docs/internal").mkdir(parents=True, exist_ok=True)
    return audit(site, ROOT / "docs/internal" / output)


if __name__ == "__main__":
    raise SystemExit(main())
