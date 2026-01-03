# CLI Contract (v1)

## Purpose
Define the command-line interface for dbl-observer.
The CLI is a tooling surface for reading and emitting observation traces,
plus rendering observation-only summaries.

Status: normative (tested)

## Guarantees
- CLI does not decide.
- CLI does not execute.
- CLI does not validate policy.
- CLI does not infer normative outcomes.
- CLI only reads, projects, and reports observational structure.

## Commands and modes
Single entrypoint:
- `dbl-observer`

Modes:
- `diagnostic` (default): read full trace, emit full trace with added observation-only diagnostics.
- `explain`: read full trace, emit a human-readable rendering of the same events and diagnostics.
- `project`: read raw artifacts, emit full trace.
- `diff`: read full trace plus reference and emit a diff rendering.
- `summary`: read full trace and emit a deterministic summary.
- `gateway`: read gateway snapshot and render observation-only lines.

## Inputs
Common flags:
- `--mode {diagnostic|explain|project|diff|summary}`
- `--input PATH|"-"` (default "-")
- `--output PATH|"-"` (default "-")
- `--reference PATH|None` (required for diff)

Input formats:
- Modes `diagnostic`, `explain`, `diff`, and `summary` require full trace rows with fields:
  - event_id, source, artifact, payload, canon_len, digest, diagnostics
- Mode `project` requires raw events with fields:
  - event_id, source, artifact, payload
  - Alternatively, a single gateway snapshot envelope (see docs/contracts/raw-input.md).
- Mode `gateway` reads from HTTP (`/snapshot`) and does not use --input.

Strict v1: inputs must match the expected schema for the selected mode. Unknown fields are rejected.

## Outputs
Mode `diagnostic`:
- Full trace rows written to output.
- Adds observation-only diagnostics labels (vocabulary bound to docs/contracts/diagnostics.md).

Mode `project`:
- Full trace rows written to output.
- Computes canon_len and digest from canonicalized payload.
- Does not invent events, does not reorder.

Mode `explain`:
- Line-oriented text rendering, one line per event, containing:
  - event_id, source, artifact, canon_len, digest, diagnostics
- May include a trace_diagnostics header line when trace-level diagnostics are present.

Mode `diff`:
- Line-oriented text rendering of differences.
- Emits a trace_diagnostics header line when trace-level diagnostics are present.
- Emits event lines only for events with reference_digest_mismatch_observed.

Mode `summary`:
- Deterministic counts by source and artifact.

## Ordering and determinism
- Ordering is the order observed in the input stream.
- CLI must not reorder events.
- Canonicalization and digests must be deterministic for identical payloads.

## Error handling (exit codes)
Exit codes describe processing status only, not correctness or authority.

- 0: processed and output emitted
- 1: input parse failure (not JSONL, wrong fields, wrong types)
- 2: canonicalization or digest computation failure (unexpected runtime failure in processing path)
- 3: output could not be written

## Non-goals
- No policy hooks
- No authentication or authorization
- No network side effects
- No automatic repair or correction
- No normative vocabulary in output (no ALLOW/DENY or equivalents)
