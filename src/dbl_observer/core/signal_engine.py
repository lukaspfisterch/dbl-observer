"""SignalEngine: pure function evaluation of signals from ProjectionIndex.

Invariants:
- SignalEngine is stateless
- All signals derived purely from ProjectionIndex
- No "since last evaluate" heuristics
- Thresholds are explicit and documented
"""
from __future__ import annotations

from typing import List

from .projection_index import ProjectionIndex
from .signal_types import Signal, SignalSeverity


# --- Thresholds (explicit, documented) ---
LATENCY_P95_WARN_MS = 5000
LATENCY_P95_CRITICAL_MS = 15000
DENY_RATE_WARN_THRESHOLD = 0.50
DENY_RATE_CRITICAL_THRESHOLD = 0.80
ERROR_CLUSTER_THRESHOLD = 3
MIN_TURNS_FOR_RATE_SIGNAL = 5


class SignalEngine:
    """Stateless signal evaluator.
    
    Call evaluate() with a ProjectionIndex to get current signals.
    This is a pure function: same ProjectionIndex always yields same signals.
    """
    
    def evaluate(self, index: ProjectionIndex) -> List[Signal]:
        """Evaluate all signal rules against current projection state.
        
        Returns a list of active signals. Order is deterministic.
        """
        signals: List[Signal] = []
        
        signals.extend(self._check_system_latency(index))
        signals.extend(self._check_thread_deny_rates(index))
        signals.extend(self._check_error_clusters(index))
        signals.extend(self._check_policy_changes(index))
        
        # Sort for determinism
        signals.sort(key=lambda s: (s.severity.value, s.scope, s.id))
        return signals

    def _check_system_latency(self, index: ProjectionIndex) -> List[Signal]:
        """Check system-wide latency P95."""
        signals = []
        latency = index.get_latency_profile()
        if latency is None:
            return signals
        
        if latency.p95 >= LATENCY_P95_CRITICAL_MS:
            signals.append(Signal(
                id="system.latency.p95.critical",
                severity=SignalSeverity.CRITICAL,
                scope="system",
                key="latency_p95",
                title="Latency P95 critical",
                detail=f"P95 latency is {latency.p95:.0f}ms (threshold: {LATENCY_P95_CRITICAL_MS}ms)",
                at_index=-1,
                evidence={"p50": latency.p50, "p95": latency.p95, "p99": latency.p99, "samples": latency.sample_count},
            ))
        elif latency.p95 >= LATENCY_P95_WARN_MS:
            signals.append(Signal(
                id="system.latency.p95.elevated",
                severity=SignalSeverity.WARN,
                scope="system",
                key="latency_p95",
                title="Latency P95 elevated",
                detail=f"P95 latency is {latency.p95:.0f}ms (threshold: {LATENCY_P95_WARN_MS}ms)",
                at_index=-1,
                evidence={"p50": latency.p50, "p95": latency.p95, "p99": latency.p99, "samples": latency.sample_count},
            ))
        
        return signals

    def _check_thread_deny_rates(self, index: ProjectionIndex) -> List[Signal]:
        """Check per-thread deny rates."""
        signals = []
        threads = index.list_threads()
        
        for thread in threads:
            if thread.turns_total < MIN_TURNS_FOR_RATE_SIGNAL:
                continue
            
            deny_rate = thread.deny_total / thread.turns_total
            
            if deny_rate >= DENY_RATE_CRITICAL_THRESHOLD:
                signals.append(Signal(
                    id=f"thread.{thread.thread_id}.deny_rate.critical",
                    severity=SignalSeverity.CRITICAL,
                    scope="thread",
                    key=thread.thread_id,
                    title="Deny rate critical",
                    detail=f"Deny rate {deny_rate*100:.0f}% over {thread.turns_total} turns",
                    at_index=thread.last_index,
                    evidence={"deny_total": thread.deny_total, "turns_total": thread.turns_total, "deny_rate": deny_rate},
                ))
            elif deny_rate >= DENY_RATE_WARN_THRESHOLD:
                signals.append(Signal(
                    id=f"thread.{thread.thread_id}.deny_rate.elevated",
                    severity=SignalSeverity.WARN,
                    scope="thread",
                    key=thread.thread_id,
                    title="Deny rate elevated",
                    detail=f"Deny rate {deny_rate*100:.0f}% over {thread.turns_total} turns",
                    at_index=thread.last_index,
                    evidence={"deny_total": thread.deny_total, "turns_total": thread.turns_total, "deny_rate": deny_rate},
                ))
        
        return signals

    def _check_error_clusters(self, index: ProjectionIndex) -> List[Signal]:
        """Check for threads with clustered execution errors."""
        signals = []
        threads = index.list_threads()
        
        for thread in threads:
            if thread.execution_error_total >= ERROR_CLUSTER_THRESHOLD:
                signals.append(Signal(
                    id=f"thread.{thread.thread_id}.error_cluster",
                    severity=SignalSeverity.WARN,
                    scope="thread",
                    key=thread.thread_id,
                    title="Execution error cluster",
                    detail=f"{thread.execution_error_total} execution errors in thread",
                    at_index=thread.last_index,
                    evidence={"error_count": thread.execution_error_total, "turns_total": thread.turns_total},
                ))
        
        return signals

    def _check_policy_changes(self, index: ProjectionIndex) -> List[Signal]:
        """Check for frequent policy changes (flip-flop)."""
        signals = []
        windows = index.get_policy_timeline()
        
        # Simple heuristic: more than 3 policy changes is notable
        if len(windows) > 3:
            signals.append(Signal(
                id="system.policy.frequent_changes",
                severity=SignalSeverity.INFO,
                scope="system",
                key="policy_changes",
                title="Frequent policy changes",
                detail=f"{len(windows)} policy versions observed",
                at_index=windows[-1].from_index if windows else -1,
                evidence={"window_count": len(windows)},
            ))
        
        return signals
