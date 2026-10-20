"""PHP API-v1 signed JSON: preserve wire number tokens, UTF-8 keys and escapes.

Not RFC 8785/JCS: the unchanged PHP signer preserves zero fractions and uses
its JSON numeric spellings. Re-decoding into ordinary floats loses those bytes.
"""

from __future__ import annotations

import json
import math
import re
from typing import Any

MAX_BYTES = 1_048_576
MAX_DEPTH = 64
_NUMBER = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\Z")


class _WireInt(int):
    token: str

    def __new__(cls, token: str) -> _WireInt:
        value = super().__new__(cls, token)
        value.token = token
        return value


class _WireFloat(float):
    token: str

    def __new__(cls, token: str) -> _WireFloat:
        value = super().__new__(cls, token)
        if not math.isfinite(value):
            raise ValueError("Non-finite number")
        value.token = token
        return value


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise ValueError("Duplicate property")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ValueError("Invalid JSON constant")


def loads(raw: bytes) -> Any:
    """Strict bounded UTF-8 JSON with lossless numeric types (still int/float)."""
    if len(raw) > MAX_BYTES:
        raise ValueError("JSON size limit")
    value: Any = json.loads(
        raw.decode("utf-8"),
        parse_int=_WireInt,
        parse_float=_WireFloat,
        parse_constant=_constant,
        object_pairs_hook=_pairs,
    )
    canonical(value)  # Also reject lone surrogates and excessive depth.
    return value


def _quote(value: str) -> str:
    value.encode("utf-8", errors="strict")
    return json.dumps(value, ensure_ascii=False).replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def canonical(value: Any, depth: int = 0) -> bytes:
    """Serialize signed/cache JSON without changing parsed numeric lexemes.

    Custom transports must use loads() or HttpResponse.from_bytes() rather than
    ordinary json.loads() for server data. Plain Python numbers are supported
    for local metadata, but cannot recover lost server numeric spellings.
    """
    if depth > MAX_DEPTH:
        raise ValueError("JSON depth limit")
    if isinstance(value, (_WireInt, _WireFloat)):
        if not _NUMBER.fullmatch(value.token):
            raise ValueError("Invalid number token")
        return value.token.encode("ascii")
    if value is None:
        return b"null"
    if isinstance(value, bool):
        return b"true" if value else b"false"
    if isinstance(value, (int, float)):
        return json.dumps(value, allow_nan=False).encode("ascii")
    if isinstance(value, str):
        return _quote(value).encode("utf-8")
    if isinstance(value, list):
        return b"[" + b",".join(canonical(v, depth + 1) for v in value) + b"]"
    if isinstance(value, dict) and all(isinstance(k, str) for k in value):
        keys = sorted(value, key=lambda k: k.encode("utf-8"))
        return (
            b"{"
            + b",".join(_quote(k).encode("utf-8") + b":" + canonical(value[k], depth + 1) for k in keys)
            + b"}"
        )
    raise ValueError("Unsupported JSON type")
