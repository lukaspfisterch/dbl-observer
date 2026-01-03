# Wire Contract (v1)

## Purpose
Define the observation trace wire format for dbl-observer.

Status: normative (tested)

## Record schema (strict)
Each line is a single JSON object with exactly these fields:
- event_id: int (monotonic ordering index)
- source: str (adapter identifier)
- artifact: str (artifact class label)
- payload: JSON-safe value (see canonicalization contract)
- canon_len: int (byte length of canonical JSON for payload)
- digest: str (sha256:<hex> over canonical JSON bytes)
- diagnostics: list[str] (observation-only labels)

Unknown fields are rejected.

## Semantics
- event_id is an observed ordering index and does not imply authority.
- source and artifact are observational labels only.
- payload is observational data only.
- canon_len and digest are determinism visibility artifacts computed from payload only.
- diagnostics are descriptive only and must not imply decisions.

Trace identity may be represented as a normal v1 event using artifact = "trace_identity".

## Ordering
- Records are processed in file order.
- The writer must not reorder events.
