# Diagnostics Contract (v1)

## Purpose
Define the observation-only diagnostics vocabulary and emission rules.

Status: normative (tested)

## Vocabulary
- duplicate_event_id_observed
- non_monotonic_event_id_observed
- ordering_gap_observed
- canon_len_mismatch_observed
- digest_mismatch_observed
- reference_length_mismatch_observed
- reference_event_id_set_mismatch_observed
- reference_order_mismatch_observed
- reference_digest_mismatch_observed

Vocabulary is frozen in v1. Additions or changes require v2.

## Emission rules
Event-level diagnostics are attached to the event record in diagnostics.
Trace-level diagnostics are computed over the full trace and are not attached to individual events.

Trace-level:
- reference_length_mismatch_observed is emitted when reference and input length differ.
- reference_event_id_set_mismatch_observed is emitted when reference and input event_id sets differ.
- reference_order_mismatch_observed is emitted when reference and input event_id order differs but sets match.

Event-level:
- canon_len_mismatch_observed and digest_mismatch_observed are attached when observed values do not match canonical recomputation.
- duplicate_event_id_observed, non_monotonic_event_id_observed, and ordering_gap_observed are attached based on event_id sequence analysis.
- reference_digest_mismatch_observed is attached when a reference trace is provided with matching event_id order and a digest mismatch is detected.

Explain output may include a trace_diagnostics header line to render trace-level diagnostics.

Diagnostics are descriptive labels only and must not imply correctness, authority, or decisions.
