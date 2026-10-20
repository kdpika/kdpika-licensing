# Runnable Sandbox examples

Install the candidate from the SDK directory: `python -m pip install .`.
Every lifecycle example explicitly uses SANDBOX and the actual SDK, not a
second implementation of its signing policy. No sample key grants access.

Set `KDP_APP_ID`, `KDP_STATE_DIR` (absolute, private, persistent directory),
`KDP_LICENSE_KEY` and optional `KDP_CUSTOMER_EMAIL` privately. Optional
`KDP_BASE_URL` is an HTTPS origin; `KDP_APP_VERSION` identifies YOUR app.
The platform's product/plan must define `pdf_export` and `seat_count` if you
want those example entitlements. They are examples, not built-in API promises.
Never put a developer management API key in these files.

Run from the SDK directory:
- `python examples/basic.py`: check or first activation; key prompted invisibly if absent.
- `python examples/session.py status|activate|check|validate|deactivate|clear-local`: one action at a time.
- `python examples/features.py`: safe boolean/numeric gating.
- `python examples/offline.py`: fresh validation; only signed grace can permit a network fallback.
- `python examples/errors.py`: plain messages and safe request ID.
- `python examples/async_usage.py`: asyncio adapter; activation key required in environment.
- `python examples/pyqt_activation.py`: install `.[qt]`; real desktop needed.
- `python examples/backend_flask.py`: install Flask separately; localhost-only, single backend license.
- `python examples/members.py`: no network; invalid-result defaults cannot grant access.

Examples preserve activation across launches. Before deleting state or uninstalling,
use `python examples/session.py deactivate` and confirm success. Clear-local
does not release a server seat. The test suite executes these code paths with a
mock transport; live requests are never part of default example tests.
