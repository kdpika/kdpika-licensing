"""Published PHP-signed vectors plus generative strict JSON regression checks."""

import json
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from kdpika_licensing._json import canonical, loads
from kdpika_licensing._verification import decode, trusted_key, verify
from kdpika_licensing.errors import SignatureVerificationError

FIXTURES = Path(__file__).parent / "fixtures/vectors"
VECTORS = json.loads((FIXTURES / "index.json").read_text(encoding="utf-8"))["vectors"]


@pytest.mark.parametrize("row", VECTORS, ids=lambda row: row["name"])
def test_shared_php_signature_vectors(row):
    key = loads((FIXTURES / row["key"]).read_bytes())
    try:
        envelope = loads((FIXTURES / row["envelope"]).read_bytes())
        verify(envelope, key)
        valid = True
    except (ValueError, SignatureVerificationError, RecursionError, UnicodeError):
        valid = False
    assert valid is row["signature_valid"]


@pytest.mark.parametrize(
    "token", ["19.0", "1.0e-7", "1.0e+20", "-0.0", "9223372036854775807", "9007199254740993", "0.00001"]
)
def test_cache_round_trip_preserves_signed_number_tokens(token):
    raw = ('{"features":{"n":' + token + '},"name":"a\\u2028b\\u2029c"}').encode()
    first = canonical(loads(raw))
    assert token.encode() in first and b"\\u2028" in first and b"\\u2029" in first
    assert canonical(loads(first)) == first
    value = loads(raw)["features"]["n"]
    assert isinstance(value, (int, float))


_scalars = (
    st.none()
    | st.booleans()
    | st.integers(min_value=-(2**63), max_value=2**63 - 1)
    | st.floats(allow_nan=False, allow_infinity=False)
    | st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=30)
)
_values = st.recursive(
    _scalars,
    lambda children: st.lists(children, max_size=4)
    | st.dictionaries(
        st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=12), children, max_size=4
    ),
    max_leaves=15,
)


@given(_values)
@settings(max_examples=200, deadline=None)
def test_lossless_canonical_roundtrip_property(value):
    raw = json.dumps(value, ensure_ascii=False, allow_nan=False).encode()
    first = canonical(loads(raw))
    assert canonical(loads(first)) == first


@pytest.mark.parametrize(
    "raw",
    [
        b'{"x":1,"x":2}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b"[]x",
        b'"\\ud800"',
        b'"\xff"',
        b'{"x":1e999}',
        b"[" * 66 + b"0" + b"]" * 66,
        b" " * 1048577,
    ],
    ids=["duplicate", "nan", "infinity", "trailing", "surrogate", "utf8", "overflow", "depth", "size"],
)
def test_reject_ambiguous_or_unbounded_json(raw):
    with pytest.raises((ValueError, UnicodeError, RecursionError)):
        loads(raw)


@pytest.mark.parametrize("value", [float("nan"), {1: "numeric object key"}, (1, 2), object()])
def test_reject_unsupported_native_values(value):
    with pytest.raises(ValueError):
        canonical(value)


@pytest.mark.parametrize("value", ["", "=", "ab+", "a", "a_", 3])
def test_strict_base64url(value):
    with pytest.raises(SignatureVerificationError):
        decode(value, 32)


def test_key_identity_and_algorithm_are_not_advisory():
    key = loads((FIXTURES / "conformance.key.json").read_bytes())
    for patch in [{"key_id": "ed25519_unrelated"}, {"algorithm": "RSA"}, {"encoding": "base64"}]:
        with pytest.raises(SignatureVerificationError):
            trusted_key({**key, **patch})
