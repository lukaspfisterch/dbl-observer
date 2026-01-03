from __future__ import annotations

import json
from typing import Any


class CanonicalizationError(Exception):
    pass


def _validate_payload(value: Any) -> None:
    if value is None or isinstance(value, (str, int, bool)):
        return
    if isinstance(value, float):
        raise CanonicalizationError("float is not allowed in canonical payloads")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError("object keys must be strings")
            _validate_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload(item)
        return
    raise CanonicalizationError("payload contains non-JSON-safe value")


def canonical_json_bytes(payload: Any) -> bytes:
    _validate_payload(payload)
    try:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except ValueError as exc:
        raise CanonicalizationError(str(exc)) from exc


def canonical_length(payload: Any) -> int:
    return len(canonical_json_bytes(payload))
