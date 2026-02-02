"""Projection types: deterministic aggregates derived from ObservedEvents.

These are pure data structures. No normative logic, no heuristics.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TurnSummary:
    """Aggregate view of a single turn (INTENT -> DECISION -> EXECUTION cycle)."""
    thread_id: str
    turn_id: str
    parent_turn_id: Optional[str] = None
    first_index: int = -1
    last_index: int = -1
    kinds: set[str] = field(default_factory=set)
    decision_result: Optional[str] = None  # ALLOW, DENY, or None
    reason_codes: List[str] = field(default_factory=list)
    provider_id: Optional[str] = None
    model_id: Optional[str] = None
    latency_ms: Optional[float] = None
    has_execution: bool = False
    has_errors: bool = False


@dataclass
class ThreadSummary:
    """Aggregate view of a thread (conversation).
    
    Note: Thread-local latency quantiles are not computed here.
    Use LatencyProfile from ProjectionIndex.get_latency_profile() for system-wide latency.
    """
    thread_id: str
    first_index: int = -1
    last_index: int = -1
    turns_total: int = 0
    deny_total: int = 0
    allow_total: int = 0
    execution_error_total: int = 0
    top_intent_types: List[tuple[str, int]] = field(default_factory=list)
    top_reason_codes: List[tuple[str, int]] = field(default_factory=list)


@dataclass
class ActorSummary:
    """Aggregate view of an actor's activity."""
    actor: str
    turns_total: int = 0
    deny_total: int = 0
    allow_total: int = 0
    errors_total: int = 0
    top_intent_types: List[tuple[str, int]] = field(default_factory=list)


@dataclass(frozen=True)
class PolicyWindow:
    """A time window where a specific policy version was active."""
    policy_id: str
    policy_version: Optional[str]
    from_index: int
    to_index: Optional[int]  # None means "still active"


@dataclass(frozen=True)
class LatencyProfile:
    """Quantile summary of latencies."""
    p50: float
    p95: float
    p99: float
    sample_count: int
