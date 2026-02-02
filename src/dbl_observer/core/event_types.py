"""ObservedEvent: the stable, minimal schema for projection and aggregation.

This is the core internal representation derived 1:1 from Gateway events.
ObservationEvent in model.py remains the UI/render layer type.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ObservedEvent:
    """Normalized gateway event for internal processing.
    
    This type is the input for EventStore and ProjectionIndex.
    It maps 1:1 from gateway event payloads with minimal normalization.
    """
    index: int
    kind: str  # INTENT, DECISION, EXECUTION, PROOF
    thread_id: str
    turn_id: str
    parent_turn_id: str | None
    actor: str
    intent_type: str
    lane: str
    stream_id: str
    created_at: str | None
    digest: str | None
    canon_len: int | None
    is_authoritative: bool | None
    payload: dict[str, Any]

    @classmethod
    def from_gateway_event(cls, event: dict[str, Any]) -> "ObservedEvent":
        """Create ObservedEvent from raw gateway event dict.
        
        This is the single conversion point from gateway format to internal format.
        """
        return cls(
            index=_get_int(event, "index"),
            kind=_get_str(event, "kind"),
            thread_id=_get_str(event, "thread_id"),
            turn_id=_get_str(event, "turn_id"),
            parent_turn_id=event.get("parent_turn_id") if isinstance(event.get("parent_turn_id"), str) else None,
            actor=_get_str(event, "actor"),
            intent_type=_get_str(event, "intent_type"),
            lane=_get_str(event, "lane"),
            stream_id=_get_str(event, "stream_id"),
            created_at=event.get("created_at") if isinstance(event.get("created_at"), str) else None,
            digest=event.get("digest") if isinstance(event.get("digest"), str) else None,
            canon_len=event.get("canon_len") if isinstance(event.get("canon_len"), int) else None,
            is_authoritative=event.get("is_authoritative") if isinstance(event.get("is_authoritative"), bool) else None,
            payload=event.get("payload") if isinstance(event.get("payload"), dict) else {},
        )


def _get_int(event: dict[str, Any], key: str) -> int:
    value = event.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        return -1
    return value


def _get_str(event: dict[str, Any], key: str) -> str:
    value = event.get(key)
    if not isinstance(value, str):
        return ""
    return value
