from pathlib import Path

from dbl_observer.canon import canonical_json_bytes
from dbl_observer.digest import sha256_digest_label, sha256_hex
from dbl_observer.model import ObservationEvent
from dbl_observer.project import read_events, write_events


def test_canon_is_stable_for_key_order():
    payload_a = {"b": 2, "a": 1, "x": {"d": 4, "c": 3}}
    payload_b = {"a": 1, "b": 2, "x": {"c": 3, "d": 4}}
    canon_a = canonical_json_bytes(payload_a)
    canon_b = canonical_json_bytes(payload_b)
    assert canon_a == canon_b
    assert sha256_hex(canon_a) == sha256_hex(canon_b)


def test_digest_is_stable_for_equivalent_payloads():
    payload_1 = {"k": "v", "n": 1, "obj": {"b": 2, "a": 1}}
    payload_2 = {"obj": {"a": 1, "b": 2}, "n": 1, "k": "v"}
    digest_1 = sha256_hex(canonical_json_bytes(payload_1))
    digest_2 = sha256_hex(canonical_json_bytes(payload_2))
    assert digest_1 == digest_2


def test_trace_roundtrip_is_stable(tmp_path: Path):
    payload_1 = {"subject": "user"}
    payload_2 = {"resource": "file"}
    canon_1 = canonical_json_bytes(payload_1)
    canon_2 = canonical_json_bytes(payload_2)
    events = [
        ObservationEvent(
            event_id=1,
            source="adapter",
            artifact="record",
            payload=payload_1,
            canon_len=len(canon_1),
            digest=sha256_digest_label(canon_1),
            diagnostics=tuple(),
        ),
        ObservationEvent(
            event_id=2,
            source="adapter",
            artifact="record",
            payload=payload_2,
            canon_len=len(canon_2),
            digest=sha256_digest_label(canon_2),
            diagnostics=tuple(),
        ),
    ]

    path = tmp_path / "trace.jsonl"
    with path.open("w", encoding="utf-8") as stream:
        write_events(events, stream)

    with path.open("r", encoding="utf-8") as stream:
        read_1 = read_events(stream, expect_raw=False)
    with path.open("r", encoding="utf-8") as stream:
        read_2 = read_events(stream, expect_raw=False)

    assert read_1 == read_2
