# Canonicalization Contract (v1)

## Purpose
Define the canonical JSON encoding used for determinism and replay visibility.

Status: normative (tested)

## Canonical JSON
Canonical JSON bytes are computed with:
- sorted object keys
- separators = (",", ":")
- ASCII-only escaping (ensure_ascii = true)
- allow_nan = false
- UTF-8 encoding for bytes

## Payload constraints
Canonical payloads are JSON-safe with the following restrictions:
- object keys must be strings
- numbers must be integers (floats are rejected)
- NaN and Infinity are rejected
- values must be JSON primitives, lists, or objects composed of these

Any payload violating these constraints is rejected.
