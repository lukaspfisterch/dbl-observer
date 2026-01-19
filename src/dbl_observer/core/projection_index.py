"""ProjectionIndex: incremental, deterministic aggregation of ObservedEvents.

Invariants:
- Expects events in gateway index order
- All state derived purely from event sequence
- Thread-safe via Lock
- Latency samples bounded to MAX_LATENCY_SAMPLES
"""
from __future__ import annotations

import threading
from collections import Counter
from typing import List, Optional

from .event_types import ObservedEvent
from .projection_types import (
    TurnSummary,
    ThreadSummary,
    ActorSummary,
    PolicyWindow,
    LatencyProfile,
)


MAX_LATENCY_SAMPLES = 5000


class ProjectionIndex:
    """Incremental projection engine over ObservedEvents.
    
    Call feed() for each event in order. Query methods return current aggregates.
    Thread-safe.
    """
    
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._turns: dict[str, TurnSummary] = {}
        self._threads: dict[str, ThreadSummary] = {}
        self._actors: dict[str, ActorSummary] = {}
        self._policy_windows: List[PolicyWindow] = []
        self._latency_samples: List[float] = []
        self._intent_type_counts: Counter[str] = Counter()
        self._reason_code_counts: Counter[str] = Counter()
        self._event_count: int = 0

    def feed(self, event: ObservedEvent) -> None:
        """Process a single event to update projections.
        
        Thread-safe. Events should be fed in gateway index order.
        """
        with self._lock:
            self._event_count += 1
            self._upsert_turn(event)
            self._upsert_thread(event)
            self._upsert_actor(event)
            self._upsert_policy(event)
            self._upsert_latency(event)

    # --- Query Methods ---

    def get_turn(self, thread_id: str, turn_id: str) -> Optional[TurnSummary]:
        """Get summary for a specific turn."""
        with self._lock:
            key = f"{thread_id}:{turn_id}"
            return self._turns.get(key)

    def get_thread(self, thread_id: str) -> Optional[ThreadSummary]:
        """Get summary for a specific thread."""
        with self._lock:
            return self._threads.get(thread_id)

    def list_threads(self) -> List[ThreadSummary]:
        """List all thread summaries, sorted by last_index descending."""
        with self._lock:
            threads = list(self._threads.values())
        threads.sort(key=lambda t: t.last_index, reverse=True)
        return threads

    def list_turns_for_thread(self, thread_id: str) -> List[TurnSummary]:
        """List all turns for a thread, sorted by first_index."""
        with self._lock:
            turns = [t for t in self._turns.values() if t.thread_id == thread_id]
        turns.sort(key=lambda t: t.first_index)
        return turns

    def list_actors(self) -> List[ActorSummary]:
        """List all actor summaries, sorted by turns_total descending."""
        with self._lock:
            actors = list(self._actors.values())
        actors.sort(key=lambda a: a.turns_total, reverse=True)
        return actors

    def get_policy_timeline(self) -> List[PolicyWindow]:
        """Get chronological list of policy windows."""
        with self._lock:
            return list(self._policy_windows)

    def get_latency_profile(self) -> Optional[LatencyProfile]:
        """Get latency quantiles from last N EXECUTION events."""
        with self._lock:
            if not self._latency_samples:
                return None
            sorted_samples = sorted(self._latency_samples)
            n = len(sorted_samples)
            return LatencyProfile(
                p50=sorted_samples[int(n * 0.50)],
                p95=sorted_samples[min(n - 1, int(n * 0.95))],
                p99=sorted_samples[min(n - 1, int(n * 0.99))],
                sample_count=n,
            )

    def get_system_metrics(self) -> dict:
        """Get system-level metrics snapshot."""
        with self._lock:
            total_turns = sum(t.turns_total for t in self._threads.values())
            total_deny = sum(t.deny_total for t in self._threads.values())
            total_allow = sum(t.allow_total for t in self._threads.values())
            deny_rate = total_deny / total_turns if total_turns > 0 else 0.0
            
            latency = self.get_latency_profile() if self._latency_samples else None
            
            return {
                "event_count": self._event_count,
                "thread_count": len(self._threads),
                "turn_count": total_turns,
                "deny_total": total_deny,
                "allow_total": total_allow,
                "deny_rate": deny_rate,
                "latency": {
                    "p50": latency.p50 if latency else None,
                    "p95": latency.p95 if latency else None,
                    "p99": latency.p99 if latency else None,
                    "sample_count": latency.sample_count if latency else 0,
                },
            }

    # --- Internal Update Methods ---

    def _upsert_turn(self, event: ObservedEvent) -> None:
        key = f"{event.thread_id}:{event.turn_id}"
        if key not in self._turns:
            self._turns[key] = TurnSummary(
                thread_id=event.thread_id,
                turn_id=event.turn_id,
                parent_turn_id=event.parent_turn_id,
                first_index=event.index,
                last_index=event.index,
            )
        turn = self._turns[key]
        
        turn.first_index = min(turn.first_index, event.index) if turn.first_index >= 0 else event.index
        turn.last_index = max(turn.last_index, event.index)
        turn.kinds.add(event.kind)
        
        if event.kind == "DECISION":
            payload = event.payload
            result = str(payload.get("decision") or payload.get("result") or "").upper()
            if result in ("ALLOW", "DENY"):
                turn.decision_result = result
            reason_codes = payload.get("reason_codes")
            if isinstance(reason_codes, list):
                turn.reason_codes = [str(r) for r in reason_codes]
                for rc in turn.reason_codes:
                    self._reason_code_counts[rc] += 1
        
        if event.kind == "EXECUTION":
            turn.has_execution = True
            payload = event.payload
            latency = payload.get("latency_ms")
            if isinstance(latency, (int, float)):
                turn.latency_ms = float(latency)
            model = payload.get("model_id")
            if isinstance(model, str):
                turn.model_id = model
            provider = payload.get("provider_id")
            if isinstance(provider, str):
                turn.provider_id = provider
            status = str(payload.get("status") or "").lower()
            if "error" in status:
                turn.has_errors = True

    def _upsert_thread(self, event: ObservedEvent) -> None:
        if event.thread_id not in self._threads:
            self._threads[event.thread_id] = ThreadSummary(
                thread_id=event.thread_id,
                first_index=event.index,
                last_index=event.index,
            )
        thread = self._threads[event.thread_id]
        
        thread.first_index = min(thread.first_index, event.index) if thread.first_index >= 0 else event.index
        thread.last_index = max(thread.last_index, event.index)
        
        if event.kind == "INTENT":
            thread.turns_total += 1
            self._intent_type_counts[event.intent_type] += 1
        
        if event.kind == "DECISION":
            payload = event.payload
            result = str(payload.get("decision") or payload.get("result") or "").upper()
            if result == "DENY":
                thread.deny_total += 1
            elif result == "ALLOW":
                thread.allow_total += 1
        
        if event.kind == "EXECUTION":
            payload = event.payload
            status = str(payload.get("status") or "").lower()
            if "error" in status:
                thread.execution_error_total += 1

    def _upsert_actor(self, event: ObservedEvent) -> None:
        if not event.actor:
            return
        if event.actor not in self._actors:
            self._actors[event.actor] = ActorSummary(actor=event.actor)
        actor = self._actors[event.actor]
        
        if event.kind == "INTENT":
            actor.turns_total += 1
        
        if event.kind == "DECISION":
            payload = event.payload
            result = str(payload.get("decision") or payload.get("result") or "").upper()
            if result == "DENY":
                actor.deny_total += 1
            elif result == "ALLOW":
                actor.allow_total += 1
        
        if event.kind == "EXECUTION":
            payload = event.payload
            status = str(payload.get("status") or "").lower()
            if "error" in status:
                actor.errors_total += 1

    def _upsert_policy(self, event: ObservedEvent) -> None:
        if event.kind != "DECISION":
            return
        payload = event.payload
        policy_id = payload.get("policy_id")
        if not isinstance(policy_id, str) or not policy_id:
            return
        policy_version = payload.get("policy_version") if isinstance(payload.get("policy_version"), str) else None
        
        # Check if this is a new policy window
        if self._policy_windows:
            last = self._policy_windows[-1]
            if last.policy_id == policy_id and last.policy_version == policy_version:
                return  # Same policy, no change
            # Close previous window
            self._policy_windows[-1] = PolicyWindow(
                policy_id=last.policy_id,
                policy_version=last.policy_version,
                from_index=last.from_index,
                to_index=event.index,
            )
        
        # Open new window
        self._policy_windows.append(PolicyWindow(
            policy_id=policy_id,
            policy_version=policy_version,
            from_index=event.index,
            to_index=None,
        ))

    def _upsert_latency(self, event: ObservedEvent) -> None:
        if event.kind != "EXECUTION":
            return
        payload = event.payload
        latency = payload.get("latency_ms")
        if isinstance(latency, (int, float)) and latency >= 0:
            self._latency_samples.append(float(latency))
            # Bounded: keep only last N samples
            if len(self._latency_samples) > MAX_LATENCY_SAMPLES:
                self._latency_samples.pop(0)
