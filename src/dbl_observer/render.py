from __future__ import annotations

from collections import Counter
from typing import Iterable, List, Sequence

from .model import ObservationEvent


def explain_lines(
    events: Sequence[ObservationEvent],
    trace_diags: Sequence[str] | None = None,
) -> List[str]:
    lines: List[str] = []
    if trace_diags:
        lines.append(f"trace_diagnostics=[{','.join(trace_diags)}]")
    for event in events:
        diagnostics = ",".join(event.diagnostics)
        lines.append(
            f"event_id={event.event_id} source={event.source} artifact={event.artifact} "
            f"canon_len={event.canon_len} digest={event.digest} "
            f"diagnostics=[{diagnostics}]"
        )
    return lines


def diff_lines(
    events: Sequence[ObservationEvent],
    trace_diags: Sequence[str] | None = None,
) -> List[str]:
    lines: List[str] = []
    if trace_diags:
        lines.append(f"trace_diagnostics=[{','.join(trace_diags)}]")
    for event in events:
        if "reference_digest_mismatch_observed" in event.diagnostics:
            diagnostics = ",".join(event.diagnostics)
            lines.append(
                f"event_id={event.event_id} source={event.source} artifact={event.artifact} "
                f"canon_len={event.canon_len} digest={event.digest} "
                f"diagnostics=[{diagnostics}]"
            )
    return lines


def summary_lines(events: Iterable[ObservationEvent]) -> List[str]:
    events_list = list(events)
    source_counts = Counter(event.source for event in events_list)
    artifact_counts = Counter(event.artifact for event in events_list)

    lines: List[str] = [f"total_events={len(events_list)}"]
    for source in sorted(source_counts):
        lines.append(f"source={source} count={source_counts[source]}")
    for artifact in sorted(artifact_counts):
        lines.append(f"artifact={artifact} count={artifact_counts[artifact]}")
    return lines
