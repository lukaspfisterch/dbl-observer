from __future__ import annotations

from collections import Counter
from typing import List, Optional, Sequence

from .model import ObservationEvent

DIAG_DUPLICATE_EVENT_ID = "duplicate_event_id_observed"
DIAG_NON_MONOTONIC_EVENT_ID = "non_monotonic_event_id_observed"
DIAG_ORDERING_GAP = "ordering_gap_observed"
DIAG_CANON_LEN_MISMATCH = "canon_len_mismatch_observed"
DIAG_DIGEST_MISMATCH = "digest_mismatch_observed"
DIAG_REFERENCE_LENGTH_MISMATCH = "reference_length_mismatch_observed"
DIAG_REFERENCE_EVENT_ID_SET_MISMATCH = "reference_event_id_set_mismatch_observed"
DIAG_REFERENCE_ORDER_MISMATCH = "reference_order_mismatch_observed"
DIAG_REFERENCE_DIGEST_MISMATCH = "reference_digest_mismatch_observed"

DIAGNOSTICS_V1 = (
    DIAG_DUPLICATE_EVENT_ID,
    DIAG_NON_MONOTONIC_EVENT_ID,
    DIAG_ORDERING_GAP,
    DIAG_CANON_LEN_MISMATCH,
    DIAG_DIGEST_MISMATCH,
    DIAG_REFERENCE_LENGTH_MISMATCH,
    DIAG_REFERENCE_EVENT_ID_SET_MISMATCH,
    DIAG_REFERENCE_ORDER_MISMATCH,
    DIAG_REFERENCE_DIGEST_MISMATCH,
)


def trace_diagnostics(
    events: Sequence[ObservationEvent],
    reference_events: Optional[Sequence[ObservationEvent]] = None,
) -> List[str]:
    if not events or reference_events is None:
        return []

    diagnostics: List[str] = []
    if len(events) != len(reference_events):
        diagnostics.append(DIAG_REFERENCE_LENGTH_MISMATCH)

    event_ids = [event.event_id for event in events]
    ref_ids = [event.event_id for event in reference_events]

    if set(event_ids) != set(ref_ids):
        diagnostics.append(DIAG_REFERENCE_EVENT_ID_SET_MISMATCH)
    elif event_ids != ref_ids:
        diagnostics.append(DIAG_REFERENCE_ORDER_MISMATCH)

    return diagnostics


def apply_trace_diagnostics(
    events: Sequence[ObservationEvent],
    reference_events: Optional[Sequence[ObservationEvent]] = None,
) -> List[ObservationEvent]:
    if not events:
        return []

    id_counts = Counter(event.event_id for event in events)
    duplicates = {event_id for event_id, count in id_counts.items() if count > 1}

    reference_digest_mismatch_ids = set()
    if reference_events is not None:
        ids_match = [event.event_id for event in events] == [
            event.event_id for event in reference_events
        ]
        if ids_match:
            for event, ref in zip(events, reference_events):
                if event.digest != ref.digest:
                    reference_digest_mismatch_ids.add(event.event_id)

    updated: List[ObservationEvent] = []
    prev_id = None
    for event in events:
        extra: List[str] = []
        if event.event_id in duplicates:
            extra.append(DIAG_DUPLICATE_EVENT_ID)
        if prev_id is not None:
            if event.event_id <= prev_id:
                extra.append(DIAG_NON_MONOTONIC_EVENT_ID)
            elif event.event_id > prev_id + 1:
                extra.append(DIAG_ORDERING_GAP)
        if event.event_id in reference_digest_mismatch_ids:
            extra.append(DIAG_REFERENCE_DIGEST_MISMATCH)

        updated.append(event.with_diagnostics(extra))
        prev_id = event.event_id

    return updated
