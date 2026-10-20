"""Inspect/install local release candidates. Never uploads or creates a tag."""

import hashlib
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from release_gate import version  # noqa: E402


def main():
    candidate = str(version())
    wheel = ROOT / f"dist/kdpika_licensing-{candidate}-py3-none-any.whl"
    sdist = ROOT / f"dist/kdpika_licensing-{candidate}.tar.gz"
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        assert "kdpika_licensing/py.typed" in names
        assert any(n.endswith("/licenses/LICENSE") for n in names)
        assert all(
            not any(x in n for x in ["__pycache__", ".DS_Store", ".env", "tests/", "docs/internal/"])
            for n in names
        )
    with tarfile.open(sdist) as archive:
        names = archive.getnames()
        for suffix in [
            "tests/conftest.py",
            "tests/fixtures/vectors/index.json",
            "docs/migration-phase1.md",
            "LICENSE",
            "mkdocs.yml",
            "SECURITY.md",
            "docs/api.md",
            "examples/basic.py",
            "examples/backend_flask.py",
            "tools/release_gate.py",
            ".github/workflows/release.yml",
        ]:
            assert any(n.endswith("/" + suffix) for n in names), suffix
        assert all(
            not any(
                part in {".env", ".venv", "__pycache__", ".tox", "node_modules"} for part in Path(n).parts
            )
            and "docs/internal/" not in n
            and "studio_soline_license_sdk.egg-info" not in n
            for n in names
        )
    workspace = Path(tempfile.mkdtemp(prefix="kdpika-artifact-install-"))
    report = {"result": "PASS", "artifacts": {}, "temporary_workspace": str(workspace), "publication": False}
    environment = {**os.environ}
    environment.pop("PYTHONPATH", None)
    for label, artifact in [("wheel", wheel), ("sdist", sdist)]:
        destination = workspace / label
        subprocess.run([sys.executable, "-m", "venv", str(destination)], check=True, capture_output=True)
        python = destination / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run(
            [str(python), "-m", "pip", "install", "--upgrade", "pip>=26.2.1,<27"],
            cwd=workspace,
            env=environment,
            check=True,
            capture_output=True,
            timeout=180,
        )
        install = subprocess.run(
            [str(python), "-m", "pip", "install", str(artifact)],
            cwd=workspace,
            env=environment,
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert install.returncode == 0, "Candidate install failed: " + install.stderr
        dependencies = subprocess.run(
            [str(python), "-m", "pip", "check"],
            cwd=workspace,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        smoke = subprocess.run(
            [str(python), str(ROOT / "tests/installed_smoke.py")],
            cwd=workspace,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert smoke.returncode == 0, smoke.stderr
        print(smoke.stdout.strip(), flush=True)
        examples = subprocess.run(
            [str(python), str(ROOT / "tests/installed_examples_smoke.py")],
            cwd=workspace,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert examples.returncode == 0, examples.stderr
        print(examples.stdout.strip(), flush=True)
        report["artifacts"][label] = {
            "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            "fresh_install": True,
            "pip_check": dependencies.stdout.strip(),
            "smoke": smoke.stdout.strip(),
            "installed_examples": examples.stdout.strip(),
            "python": str(python),
        }
    (ROOT / "docs/internal").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs/internal/artifact-verification-release.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps({"result": "PASS", "artifacts": 2, "published": False}))


if __name__ == "__main__":
    main()
