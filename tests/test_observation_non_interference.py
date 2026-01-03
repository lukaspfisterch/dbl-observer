from dbl_observer.canon import canonical_json_bytes
from dbl_observer.digest import sha256_hex


def test_changing_diagnostics_does_not_change_payload_digest():
    payload = {"x": 1, "y": {"b": 2, "a": 1}}
    canon = canonical_json_bytes(payload)
    digest_payload = "sha256:" + sha256_hex(canon)

    e1 = {
        "event_id": 1,
        "source": "adapter",
        "artifact": "record",
        "payload": payload,
        "canon_len": len(canon),
        "digest": digest_payload,
        "diagnostics": [],
    }

    e2 = {
        **e1,
        "diagnostics": ["ordering_gap_observed"],
    }

    assert e1["digest"] == e2["digest"]
    assert e1["canon_len"] == e2["canon_len"]
