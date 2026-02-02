"""Tests for core projection modules."""
from __future__ import annotations

import pytest

from dbl_observer.core.event_types import ObservedEvent
from dbl_observer.core.event_store import EventStore
from dbl_observer.core.projection_index import ProjectionIndex
from dbl_observer.core.signal_engine import SignalEngine


def _make_event(
    index: int,
    kind: str,
    thread_id: str = "thread-1",
    turn_id: str = "turn-1",
    decision: str | None = None,
    latency_ms: float | None = None,
    status: str | None = None,
) -> ObservedEvent:
    payload = {}
    if decision:
        payload["decision"] = decision
    if latency_ms is not None:
        payload["latency_ms"] = latency_ms
    if status:
        payload["status"] = status
    
    return ObservedEvent(
        index=index,
        kind=kind,
        thread_id=thread_id,
        turn_id=turn_id,
        parent_turn_id=None,
        actor="test-actor",
        intent_type="test",
        lane="default",
        stream_id="default",
        created_at=None,
        digest=None,
        canon_len=None,
        is_authoritative=None,
        payload=payload,
    )


class TestEventStore:
    def test_append_and_retrieve(self):
        store = EventStore()
        e1 = _make_event(0, "INTENT")
        e2 = _make_event(1, "DECISION", decision="ALLOW")
        
        store.append(e1)
        store.append(e2)
        
        assert store.count() == 2
        assert store.last_index() == 1
        
        all_events = store.all()
        assert len(all_events) == 2
        assert all_events[0].kind == "INTENT"
        assert all_events[1].kind == "DECISION"

    def test_thread_index(self):
        store = EventStore()
        store.append(_make_event(0, "INTENT", thread_id="t1"))
        store.append(_make_event(1, "INTENT", thread_id="t2"))
        store.append(_make_event(2, "DECISION", thread_id="t1", decision="ALLOW"))
        
        t1_events = store.thread("t1")
        assert len(t1_events) == 2
        
        t2_events = store.thread("t2")
        assert len(t2_events) == 1

    def test_turn_index(self):
        store = EventStore()
        store.append(_make_event(0, "INTENT", thread_id="t1", turn_id="turn-a"))
        store.append(_make_event(1, "DECISION", thread_id="t1", turn_id="turn-a", decision="ALLOW"))
        store.append(_make_event(2, "INTENT", thread_id="t1", turn_id="turn-b"))
        
        turn_a = store.turn("t1", "turn-a")
        assert len(turn_a) == 2
        
        turn_b = store.turn("t1", "turn-b")
        assert len(turn_b) == 1


class TestProjectionIndex:
    def test_turn_summary(self):
        index = ProjectionIndex()
        index.feed(_make_event(0, "INTENT", turn_id="t1"))
        index.feed(_make_event(1, "DECISION", turn_id="t1", decision="ALLOW"))
        index.feed(_make_event(2, "EXECUTION", turn_id="t1", latency_ms=150.0))
        
        turn = index.get_turn("thread-1", "t1")
        assert turn is not None
        assert turn.decision_result == "ALLOW"
        assert turn.has_execution is True
        assert turn.latency_ms == 150.0

    def test_thread_summary_deny_count(self):
        index = ProjectionIndex()
        index.feed(_make_event(0, "INTENT", turn_id="t1"))
        index.feed(_make_event(1, "DECISION", turn_id="t1", decision="DENY"))
        index.feed(_make_event(2, "INTENT", turn_id="t2"))
        index.feed(_make_event(3, "DECISION", turn_id="t2", decision="ALLOW"))
        
        thread = index.get_thread("thread-1")
        assert thread is not None
        assert thread.turns_total == 2
        assert thread.deny_total == 1
        assert thread.allow_total == 1

    def test_latency_profile(self):
        index = ProjectionIndex()
        for i in range(100):
            index.feed(_make_event(i * 2, "INTENT", turn_id=f"t{i}"))
            index.feed(_make_event(i * 2 + 1, "EXECUTION", turn_id=f"t{i}", latency_ms=float(100 + i)))
        
        profile = index.get_latency_profile()
        assert profile is not None
        assert profile.sample_count == 100
        assert profile.p50 >= 100  # Median should be around 150
        assert profile.p95 >= 100

    def test_determinism_same_events_same_result(self):
        """Same events in same order must produce identical projections."""
        events = [
            _make_event(0, "INTENT", turn_id="t1"),
            _make_event(1, "DECISION", turn_id="t1", decision="ALLOW"),
            _make_event(2, "EXECUTION", turn_id="t1", latency_ms=200.0),
        ]
        
        index1 = ProjectionIndex()
        index2 = ProjectionIndex()
        
        for e in events:
            index1.feed(e)
            index2.feed(e)
        
        t1 = index1.get_turn("thread-1", "t1")
        t2 = index2.get_turn("thread-1", "t1")
        
        assert t1 is not None and t2 is not None
        assert t1.decision_result == t2.decision_result
        assert t1.latency_ms == t2.latency_ms
        assert t1.has_execution == t2.has_execution


class TestSignalEngine:
    def test_no_signals_on_healthy_system(self):
        index = ProjectionIndex()
        # Few events, low latency, no denies
        for i in range(3):
            index.feed(_make_event(i * 2, "INTENT", turn_id=f"t{i}"))
            index.feed(_make_event(i * 2 + 1, "EXECUTION", turn_id=f"t{i}", latency_ms=100.0))
        
        engine = SignalEngine()
        signals = engine.evaluate(index)
        
        # Should have no critical or warn signals
        critical = [s for s in signals if s.severity.value == "critical"]
        warn = [s for s in signals if s.severity.value == "warn"]
        assert len(critical) == 0
        assert len(warn) == 0

    def test_deny_rate_signal(self):
        index = ProjectionIndex()
        # 6 turns, 5 denies = 83% deny rate
        for i in range(6):
            index.feed(_make_event(i * 2, "INTENT", turn_id=f"t{i}"))
            decision = "DENY" if i < 5 else "ALLOW"
            index.feed(_make_event(i * 2 + 1, "DECISION", turn_id=f"t{i}", decision=decision))
        
        engine = SignalEngine()
        signals = engine.evaluate(index)
        
        deny_signals = [s for s in signals if "deny_rate" in s.id]
        assert len(deny_signals) >= 1
        assert deny_signals[0].severity.value in ("warn", "critical")

    def test_pure_function_same_index_same_signals(self):
        """SignalEngine must be a pure function: same input, same output."""
        index = ProjectionIndex()
        for i in range(10):
            index.feed(_make_event(i * 2, "INTENT", turn_id=f"t{i}"))
            index.feed(_make_event(i * 2 + 1, "DECISION", turn_id=f"t{i}", decision="DENY"))
        
        engine = SignalEngine()
        signals1 = engine.evaluate(index)
        signals2 = engine.evaluate(index)
        
        assert len(signals1) == len(signals2)
        for s1, s2 in zip(signals1, signals2):
            assert s1.id == s2.id
            assert s1.severity == s2.severity
