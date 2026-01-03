# Raw Input Contract (v1)

## Purpose
Define the raw artifact input format accepted by project mode.

Status: normative (tested)

## Record schema (strict)
Each line is a single JSON object with exactly these fields:
- event_id: int
- source: str
- artifact: str
- payload: JSON-safe value (see canonicalization contract)

Unknown fields are rejected.

## Gateway snapshot envelope (optional)
Project mode also accepts a single JSON object shaped like a gateway snapshot:
- events: list of gateway event objects
- offset, limit: int (optional)
Each gateway event is projected into a raw record with:
- event_id: event.index
- source: "dbl-gateway"
- artifact: "gateway_event"
- payload: the gateway event object (unchanged)

## Semantics
Raw events are observational inputs only. Project mode computes canon_len and digest and emits the wire format.
