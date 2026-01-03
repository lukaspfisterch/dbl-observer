# Minimal design for dbl-observer

This document defines the minimal architectural design for dbl-observer. It is observation-only and must not introduce normativity.

## Module boundaries
- Source adapters: read existing artifacts and emit observations.
- Projector: projects observations into a unified trace without interpretation.
- Canonicalization: produces stable, observable representations of payloads for replay visibility.
- Digest: computes a deterministic digest over canonical payloads for comparison only.
- Diagnostics: emits observation-only diagnostics about ordering and replay visibility.
- Renderer: renders diagnostics and trace summaries for diagnostic, explain, diff, and summary modes.

## Data model (conceptual)
ObservationEvent (one line in the wire format):
- event_id: ordered index for the observed event.
- source: adapter identifier for the origin artifact.
- artifact: observational label for the artifact class.
- payload: observation payload as received.
- canon_len: length of the canonicalized payload.
- digest: deterministic digest of the canonicalized payload.
- diagnostics: observation-only notes attached to this event.

ObservationTrace:
- ordered list of ObservationEvent entries.
- replay visibility derived from stable ordering and digest comparison.

## Determinism strategy
- Canonicalize each payload to a stable representation.
- Compute a deterministic digest over that canonical payload for replay comparison.
- Use ordering and digest equality only for visibility; no decisions, judgments, or policy logic are derived from them.
