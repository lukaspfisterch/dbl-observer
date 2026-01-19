"""EventStore: append-only in-memory store for ObservedEvents.

Provides indexed access by thread_id, turn_id, actor.
Thread-safe via Lock for concurrent read/write.
"""
from __future__ import annotations

import threading
from typing import List, Optional

from .event_types import ObservedEvent


class EventStore:
    """Append-only store for ObservedEvents with indexed access.
    
    Invariants:
    - Events are stored in append order (expected to be gateway index order)
    - All mutations happen under lock
    - Readers also acquire lock briefly for consistent reads
    """
    
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: List[ObservedEvent] = []
        self._by_thread: dict[str, List[int]] = {}
        self._by_turn: dict[str, List[int]] = {}
        self._by_actor: dict[str, List[int]] = {}

    def append(self, event: ObservedEvent) -> None:
        """Append a single event to the store.
        
        Thread-safe. Events should be appended in gateway index order.
        """
        with self._lock:
            idx = len(self._events)
            self._events.append(event)
            
            # Index by thread_id
            if event.thread_id:
                if event.thread_id not in self._by_thread:
                    self._by_thread[event.thread_id] = []
                self._by_thread[event.thread_id].append(idx)
            
            # Index by turn_id (composite key)
            turn_key = f"{event.thread_id}:{event.turn_id}"
            if turn_key not in self._by_turn:
                self._by_turn[turn_key] = []
            self._by_turn[turn_key].append(idx)
            
            # Index by actor
            if event.actor:
                if event.actor not in self._by_actor:
                    self._by_actor[event.actor] = []
                self._by_actor[event.actor].append(idx)

    def all(self) -> List[ObservedEvent]:
        """Return all events in append order.
        
        Thread-safe. Returns a copy.
        """
        with self._lock:
            return list(self._events)

    def thread(self, thread_id: str) -> List[ObservedEvent]:
        """Return all events for a specific thread_id.
        
        Thread-safe. Returns a copy.
        """
        with self._lock:
            indices = self._by_thread.get(thread_id, [])
            return [self._events[i] for i in indices]

    def turn(self, thread_id: str, turn_id: str) -> List[ObservedEvent]:
        """Return all events for a specific turn.
        
        Thread-safe. Returns a copy.
        """
        with self._lock:
            key = f"{thread_id}:{turn_id}"
            indices = self._by_turn.get(key, [])
            return [self._events[i] for i in indices]

    def actor(self, actor: str) -> List[ObservedEvent]:
        """Return all events for a specific actor.
        
        Thread-safe. Returns a copy.
        """
        with self._lock:
            indices = self._by_actor.get(actor, [])
            return [self._events[i] for i in indices]

    def last_index(self) -> Optional[int]:
        """Return the index field of the last appended event, or None if empty.
        
        Thread-safe.
        """
        with self._lock:
            if not self._events:
                return None
            return self._events[-1].index

    def count(self) -> int:
        """Return total number of events in store.
        
        Thread-safe.
        """
        with self._lock:
            return len(self._events)

    def thread_ids(self) -> List[str]:
        """Return list of all known thread_ids.
        
        Thread-safe.
        """
        with self._lock:
            return list(self._by_thread.keys())

    def actor_ids(self) -> List[str]:
        """Return list of all known actors.
        
        Thread-safe.
        """
        with self._lock:
            return list(self._by_actor.keys())
