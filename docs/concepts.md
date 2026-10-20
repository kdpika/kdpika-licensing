# Concepts

| Concept | Meaning |
|---|---|
| Public App ID | Public software identifier, not an API credential |
| Customer key | Private purchase credential supplied by the customer |
| Installation | Stable randomly generated identity scoped to origin/App ID/environment |
| Activation token | Stored private credential for validate/deactivate; never log it |
| Signed license | Ed25519-authenticated response plus binding and time policy |
| Feature | Product-plan entitlement, interpreted by your application |
| Sandbox / Live | Explicit access separation; TEST/production aliases normalize |

The compatibility default is LIVE. Examples always explicitly choose SANDBOX.
A developer management API key is neither required nor suitable in a client app.

Lifecycle: activate once, check before protected work, validate when needed,
deactivate to release. check may use verified cache before next-validation;
validate requests online but can use authentic grace after a network failure.
A refused HTTP response is not an offline outage fallback.

A result with valid=True from deactivate acknowledges release, not access.
Constructing LicenseResult manually does not verify data. Client-level feature
helpers check again; result-level helpers re-evaluate deadlines. Signed status,
bindings, expiry and clock/grace all matter.

The JSON contract is PHP's unchanged sorted JSON encoding, not RFC 8785/JCS.
Use the SDK decoder; numeric spelling such as 19.0 and exponents is signed data.
