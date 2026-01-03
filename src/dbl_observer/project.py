from __future__ import annotations

import json
from typing import IO, Any, Iterable, List

from .canon import canonical_json_bytes
from .digest import sha256_digest_label
from .diagnostics import DIAG_CANON_LEN_MISMATCH, DIAG_DIGEST_MISMATCH
from .model import ObservationEvent


def read_events(stream: IO[str], expect_raw: bool) -> List[ObservationEvent]:
    events: List[ObservationEvent] = []
    for line_no, line in enumerate(stream, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {line_no}: invalid json") from exc
        if expect_raw and line_no == 1 and _is_snapshot_envelope(obj):
            events = _parse_snapshot_envelope(obj, line_no)
            for rest_line_no, rest_line in enumerate(stream, start=line_no + 1):
                if rest_line.strip():
                    raise ValueError(
                        f"line {rest_line_no}: unexpected content after snapshot envelope"
                    )
            return events
        events.append(_parse_event(obj, expect_raw=expect_raw, line_no=line_no))
    return events


def write_events(events: Iterable[ObservationEvent], stream: IO[str]) -> None:
    for event in events:
        obj = {
            "event_id": event.event_id,
            "source": event.source,
            "artifact": event.artifact,
            "payload": event.payload,
            "canon_len": event.canon_len,
            "digest": event.digest,
            "diagnostics": list(event.diagnostics),
        }
        stream.write(
            json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        )
        stream.write("\n")


def _parse_event(obj: Any, expect_raw: bool, line_no: int) -> ObservationEvent:
    if not isinstance(obj, dict):
        raise ValueError(f"line {line_no}: expected object")

    raw_keys = {"event_id", "source", "artifact", "payload"}
    full_keys = {"event_id", "source", "artifact", "payload", "canon_len", "digest", "diagnostics"}

    keys = set(obj.keys())
    if expect_raw:
        if keys != raw_keys:
            raise ValueError(f"line {line_no}: expected raw event fields")
        event_id = _parse_event_id(obj["event_id"], line_no)
        source = _parse_str(obj["source"], "source", line_no)
        artifact = _parse_str(obj["artifact"], "artifact", line_no)
        payload = obj["payload"]
        canon_bytes = canonical_json_bytes(payload)
        canon_len = len(canon_bytes)
        digest = sha256_digest_label(canon_bytes)
        diagnostics: List[str] = []
    else:
        if keys != full_keys:
            raise ValueError(f"line {line_no}: expected trace event fields")
        event_id = _parse_event_id(obj["event_id"], line_no)
        source = _parse_str(obj["source"], "source", line_no)
        artifact = _parse_str(obj["artifact"], "artifact", line_no)
        payload = obj["payload"]
        canon_len = _parse_int(obj["canon_len"], "canon_len", line_no)
        digest = _parse_str(obj["digest"], "digest", line_no)
        diagnostics = _parse_diagnostics(obj["diagnostics"], line_no)

        canon_bytes = canonical_json_bytes(payload)
        observed_len = len(canon_bytes)
        observed_digest = sha256_digest_label(canon_bytes)
        if canon_len != observed_len:
            diagnostics.append(DIAG_CANON_LEN_MISMATCH)
        if digest != observed_digest:
            diagnostics.append(DIAG_DIGEST_MISMATCH)

    return ObservationEvent(
        event_id=event_id,
        source=source,
        artifact=artifact,
        payload=payload,
        canon_len=canon_len,
        digest=digest,
        diagnostics=tuple(diagnostics),
    )


def _is_snapshot_envelope(obj: Any) -> bool:
    if not isinstance(obj, dict):
        return False
    if "events" not in obj:
        return False
    if not isinstance(obj.get("events"), list):
        return False
    offset = obj.get("offset")
    limit = obj.get("limit")
    if isinstance(offset, bool) or (offset is not None and not isinstance(offset, int)):
        return False
    if isinstance(limit, bool) or (limit is not None and not isinstance(limit, int)):
        return False
    return True


def _parse_snapshot_envelope(obj: dict[str, Any], line_no: int) -> List[ObservationEvent]:
    events: List[ObservationEvent] = []
    for item in obj.get("events", []):
        if not isinstance(item, dict):
            raise ValueError(f"line {line_no}: snapshot events must be objects")
        event_id = item.get("index")
        if isinstance(event_id, bool) or not isinstance(event_id, int):
            raise ValueError(f"line {line_no}: snapshot event index must be int")
        raw = {
            "event_id": event_id,
            "source": "dbl-gateway",
            "artifact": "gateway_event",
            "payload": item,
        }
        events.append(_parse_event(raw, expect_raw=True, line_no=line_no))
    return events


def _parse_event_id(value: Any, line_no: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"line {line_no}: event_id must be int")
    return value


def _parse_int(value: Any, field: str, line_no: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"line {line_no}: {field} must be int")
    return value


def _parse_str(value: Any, field: str, line_no: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"line {line_no}: {field} must be str")
    return value


def _parse_diagnostics(value: Any, line_no: int) -> List[str]:
    if not isinstance(value, list):
        raise ValueError(f"line {line_no}: diagnostics must be list")
    diagnostics: List[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"line {line_no}: diagnostics must be list of str")
        diagnostics.append(item)
    return diagnostics
