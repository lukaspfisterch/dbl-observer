from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Tuple


@dataclass(frozen=True)
class ObservationEvent:
    event_id: int
    source: str
    artifact: str
    payload: Any
    canon_len: int
    digest: str
    diagnostics: Tuple[str, ...]

    def with_diagnostics(self, extra: Iterable[str]) -> "ObservationEvent":
        combined = tuple(self.diagnostics) + tuple(extra)
        return ObservationEvent(
            event_id=self.event_id,
            source=self.source,
            artifact=self.artifact,
            payload=self.payload,
            canon_len=self.canon_len,
            digest=self.digest,
            diagnostics=combined,
        )
