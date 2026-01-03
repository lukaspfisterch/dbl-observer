# Digest Contract (v1)

## Purpose
Define deterministic digest formation for observation payloads.

Status: normative (tested)

## Digest formation
- digest = "sha256:" + hex(sha256(canonical_json_bytes(payload)))
- hex is lowercase and fixed-length.

Digest is observational and must not be interpreted as a decision.
