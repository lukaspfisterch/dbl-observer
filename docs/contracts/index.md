# Contract Index

This document enumerates the contract surfaces for dbl-observer and their stability.

Status: normative (tested) for v1 surfaces; v2 is conceptual.

## Contract surfaces
Wire contracts:
- Observation trace (v1, stable)
- Raw artifact input for project mode (v1, stable)

Processing contracts:
- Canonicalization (v1, stable)
- Digest formation (v1, stable)
- Diagnostics vocabulary and emission rules (v1, stable)

CLI contracts:
- CLI flags, modes, exit codes, and I/O behavior (v1, stable)
UI contracts:
- UI wire protocol (v1, stable)

## Versioning policy
v1 is strict and schema-locked. Unknown fields are rejected.
v2 is reserved for evolvable traces with explicit schema_version and optional trace-level metadata.
