# Owner release procedure

**No registry release has been published.** The owner authorized the initial
private source upload to https://github.com/kdpika/kdpika-licensing. These
instructions do not authorize PyPI/TestPyPI publication, release tags, changing
repository visibility or hosted downloads. Complete all gates before release.

## 1. Resolve owner decisions

- Approve final package/import/version and support contact.
- Replace the proprietary information-only LICENSE with owner-approved actual
  usage/redistribution terms; do not select an open-source grant without approval.
- Set release-config.json approvals true only after those decisions. Set
  approved_license_sha256 to the actual approved file hash:
  `python -c "import hashlib,pathlib;print(hashlib.sha256(pathlib.Path('LICENSE').read_bytes()).hexdigest())"`.
  The gate explicitly refuses the old information-only notice.
- The confirmed repository is **kdpika/kdpika-licensing**, currently private.
  release-config.json and source/issues metadata use this actual identity;
  CODEOWNERS names @kdpika. Do not change visibility without owner permission.
- Confirm support_email and the remaining release approvals; no registry/CI
  success badge is added until the corresponding release/check actually exists.
- Recheck PyPI name availability immediately before publication. The name's
  JSON endpoint returned 404 on 2026-10-20, which is not a reservation.

## 2. Prepare a dedicated SDK repository safely

In the platform workspace, `.github/` lives inside sdk/python deliberately.
The dedicated repository has the **contents of sdk/python at its root**, so
GitHub recognizes its workflows. The PHP monorepository is not pushed.

Do NOT push this whole platform repository: it contains unrelated source,
deployment data and possible private local files. Use a reviewed SDK source
archive/allowlisted export, exclude docs/internal and local caches/egg-info/
virtualenvs, and scan it before your first owner-authorized push. The sdist
contains the SDK source, docs, examples, tools and workflow templates but no
internal reports or .env files.

At the dedicated root: pyproject.toml, src/, tests/, examples/, docs/, tools/
and .github/ are siblings. No workflow working-directory rewrite is needed.

## 3. One-time GitHub and Trusted Publisher setup

For both GitHub environments **testpypi** and **pypi**:
require human reviewers, prevent self-approval if available, and restrict
deployment to reviewed release tags. Protect main and release tags/rulesets.
If your GitHub plan cannot enforce reviewers, stop and arrange an equivalent
owner-controlled release approval process before enabling publishing.

Enable MFA on PyPI/TestPyPI and protect GitHub. Create a pending Trusted
Publisher (or normal publisher if the project already exists) separately on
each index. Use these exact matching fields:

| Field | Value |
|---|---|
| Project | kdpika-licensing (owner-confirmed name) |
| GitHub owner | kdpika |
| Repository | kdpika-licensing |
| Workflow filename | release.yml |
| Environment on TestPyPI | testpypi |
| Environment on production PyPI | pypi |

The workflow uses OIDC through the SHA-pinned PyPA publishing action; no stored
API token, username or password. Only publishing jobs have id-token:write;
build/test jobs have contents:read. The publish jobs download only artifacts
from their successful current-run quality build and do not execute the source.

Upstream references:
[PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/),
[GitHub environments](https://docs.github.com/en/actions/deployment/targeting-different-environments/managing-environments-for-deployment).
Action SHAs were resolved with git ls-remote on 2026-10-20; Dependabot updates
actions/pip weekly. Review changes rather than blindly merging them.

## 4. Local and remote verification (no publishing yet)

Use a private clean virtualenv with Python 3.11–3.14; update pip first.

~~~bash
python -m pip install --upgrade "pip>=26.2.1,<27"
python -m pip install '.[dev,docs,test]'
ruff check src tests tools examples
ruff format --check src tests tools examples
mypy --strict src
python -m pytest --cov --cov-report=term-missing
tox -e py311,py312,py313,py314
mkdocs build --strict
python -m build
python -m twine check dist/*
python tools/verify_artifacts.py
python tools/audit_dependencies.py
python tools/audit_dependencies.py --tooling
~~~

CI must run the 12-combination Linux/macOS/Windows matrix and quality job.
Local macOS passing does not establish the other OS results. Optional Qt,
native vault and packaged app tests still need target-platform acceptance.
The base audit targets the installed wheel dependency set; the --tooling audit
separately checks the dedicated dev/docs/test environment. The unpublished own
package registry lookup is explicitly skipped. Optional Qt/native-keyring
acceptance is separate and is not certified by either advisory lookup.

An owner gate check (with your real repository, after legal/identity decisions):
`python tools/release_gate.py --tag v1.1.0rc1 --repository kdpika/kdpika-licensing`.
It must fail with the checked-in unresolved config. Tests use synthetic config
to verify both pass/fail routing; they do not approve the real release.

## 5. Owner-only TestPyPI dry run

The following commands create/push a tag and trigger publishing. **Do not run
until explicit owner authorization. They were NOT run during preparation.**
Start from a clean reviewed commit and source version 1.1.0rc1:

~~~bash
git tag -a v1.1.0rc1 -m "KDPika Python SDK 1.1.0rc1"
git push origin v1.1.0rc1
~~~

The release gate checks exact source/tag/repository identity. CI is called
again for the tag. A pre-release routes only to protected testpypi; approve
that environment only after reviewing results. Production remains untouched.

After the upload, in a fresh virtualenv:

~~~bash
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ "kdpika-licensing==1.1.0rc1"
python -c "import kdpika_licensing; print(kdpika_licensing.__version__)"
~~~

Using extra-index-url lets either index satisfy dependencies (dependency-
confusion risk). Prefer installing approved cryptography dependencies from
PyPI first, then installing the exact candidate from TestPyPI with --no-deps:

~~~bash
python -m pip install --index-url https://pypi.org/simple/ "cryptography>=50.0.2,<51"
python -m pip install --index-url https://test.pypi.org/simple/ --no-deps "kdpika-licensing==1.1.0rc1"
python -m pip check
~~~

Run the installed mocked lifecycle smoke and your disposable Sandbox acceptance
only with private environment credentials. No developer API key is required.
Check the downloaded artifact hash against reviewed build evidence.

## 6. Owner-only production release

After TestPyPI and target-OS acceptance, deliberately change source version and
changelog to the owner-approved stable version (for example 1.1.0), review it,
update approval config, rerun all checks and commit. Do not relabel an existing
immutable index file or reuse a published version.

Only then, with explicit publication approval:

~~~bash
git tag -a v1.1.0 -m "KDPika Python SDK 1.1.0"
git push origin v1.1.0
~~~

Stable tags route only to protected pypi. Review the exact artifacts and approve
the production environment. The workflow does not create a GitHub public
release or push further commits. No remote action has been executed here.

## 7. Verify and coordinate public documentation

Install the exact stable version from PyPI in a fresh venv; import, print
version and run the signed mock lifecycle plus disposable Sandbox lifecycle.
Inspect metadata/typing/license, optional extras and all OS CI results.

Only after publication, update the platform Python SDK page at
https://licensing.kdpika.com/docs/v1/sdks/python: approved version, pip install
instructions, new import, migration/compatibility notes and genuine registry/
repository links. Update source ZIP/versioned archives deliberately, not by
running an unrelated monorepository docs build against this unapproved candidate.
Keep API v1 documentation linked rather than duplicating its contract.

If a release is defective, stop rollouts, publish a corrected new version and
consider yanking the defective version with owner authorization; do not silently
replace immutable files or promise a rollback of customer activations.
