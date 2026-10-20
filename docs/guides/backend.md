# Backend services

The source includes examples/backend_flask.py. Install Flask separately for
that example; it is not a required SDK runtime dependency. Set private KDP_*
configuration for **this backend's own software license** and run locally.

The localhost POST /export demo checks a fresh valid/signature-valid result
and pdf_export before returning demonstration metadata. It does not export a
real file and is not a customer-license API. There is no public HTTP route
taking keys or arbitrary installation IDs.

Before deploying any web service, add your own authenticated users, per-user/
tenant authorization, rate limiting, TLS and operational controls. Never map
all customers to one installation identity. Management/fulfillment API keys
belong on a trusted server using the actual server API contract, not this
client's activation interface.
