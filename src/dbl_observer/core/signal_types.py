"""Signal types: NON_NORMATIVE attention markers.

Signals are derived purely from ProjectionIndex.
They do not represent decisions, only observations.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SignalSeverity(str, Enum):
    INFO = "info"
    WARN = "warn"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Signal:
    """A non-normative attention marker.
    
    Signals are descriptive observations, not decisions.
    They help focus attention but do not imply correctness or authority.
    """
    id: str
    severity: SignalSeverity
    scope: str  # system, thread, turn, actor, policy
    key: str  # the entity key (thread_id, actor, etc.)
    title: str
    detail: str
    at_index: int
    evidence: dict[str, Any]
