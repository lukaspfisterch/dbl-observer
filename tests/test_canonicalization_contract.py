from __future__ import annotations

import math

import pytest

from dbl_observer.canon import CanonicalizationError, canonical_json_bytes


def test_canonical_rejects_float() -> None:
    with pytest.raises(CanonicalizationError, match="float is not allowed"):
        canonical_json_bytes({"x": 1.5})


def test_canonical_rejects_nan() -> None:
    with pytest.raises(CanonicalizationError, match="float is not allowed"):
        canonical_json_bytes({"x": math.nan})


def test_canonical_rejects_non_str_keys() -> None:
    with pytest.raises(CanonicalizationError, match="object keys must be strings"):
        canonical_json_bytes({1: "x"})  # type: ignore[dict-item]


def test_canonical_escapes_unicode() -> None:
    data = {"name": "M\u00fcnchen"}
    canon = canonical_json_bytes(data)
    assert b"\\u00fc" in canon
