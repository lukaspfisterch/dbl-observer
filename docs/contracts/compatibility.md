# Compatibility Contract (v1)

## Versioning
v1 is strict and schema-locked. Unknown fields are rejected.

Status: normative (tested) for v1; v2 is conceptual.

## Forward and backward compatibility
- Forward: v1 readers reject unknown fields.
- Backward: v1 writers emit only the v1 schema.

## Planned v2 scope
v2 is reserved for evolvable traces with explicit schema_version and optional trace-level metadata. v2 is not implemented in v1 tooling.

Reserved optional metadata fields for v2:
- schema_version (int)
- trace_id (opaque string)
- observed_at (string timestamp, observational)
- source (opaque emitter label)
- meta (object, observational)
