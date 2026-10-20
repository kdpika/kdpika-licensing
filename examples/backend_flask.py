"""Single-customer backend example, not a multi-tenant authentication system.

Install Flask separately. KDP_* values belong to THIS backend's own software
license, never a caller-supplied identity or another tenant. A real service must
add its own authenticated users, authorization and rate limits before exposure.
"""

import os

from _common import configured_client, required

from kdpika_licensing import LicenseClient


def export_allowed(client: LicenseClient) -> bool:
    result = client.check()
    return bool(result.valid and result.signature_valid and result.feature("pdf_export"))


def create_app():
    from flask import Flask, jsonify

    app = Flask(__name__)
    client = configured_client()
    # Explicit startup configuration, never an HTTP activation route.
    if not client.activated:
        result = client.activate(required("KDP_LICENSE_KEY"), os.getenv("KDP_CUSTOMER_EMAIL"))
        if not result.valid or not result.signature_valid:
            raise RuntimeError("Backend license unavailable; contact the software publisher.")

    @app.post("/export")
    def export():
        # Demonstration returns metadata only; put actual protected work here.
        if not export_allowed(client):
            return jsonify({"error": "This feature is unavailable."}), 403
        return jsonify({"permitted": True, "note": "Demo only; no file generated."})

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
