# Command-line applications

The SDK intentionally does not install a global CLI entry point. The tested
session script is explicit and keeps secrets out of command-line arguments.

~~~bash
python examples/session.py status
python examples/session.py activate
python examples/session.py check
python examples/session.py validate
python examples/session.py deactivate
~~~

Set KDP_APP_ID and persistent KDP_STATE_DIR privately. Activation reads
KDP_LICENSE_KEY or uses a hidden getpass prompt. KDP_CUSTOMER_EMAIL is optional
unless the server product requires it. All actions explicitly use Sandbox.

status reports token presence/storage only, not permission. clear-local erases
credentials/cache but preserves identity and does NOT release the server seat.
Do not clear uncertain activations to work around limits. The scripts return
0 for a successful command, 1 for refused lifecycle decisions and 2 for
configuration/storage setup failures. Deactivation success grants no features.
