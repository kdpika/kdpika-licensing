"""Audit actual fresh base installation from verify_artifacts.py; no publishing."""

import argparse
import json
import subprocess
import sys
import sysconfig
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pip_audit",
            "--path",
            site,
            "--progress-spinner",
            "off",
            "--format",
            "json",
            "--output",
            str(ROOT / "docs/internal" / output),
        ],
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
