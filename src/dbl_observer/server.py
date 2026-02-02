from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from .project import project_raw_items, parse_trace_items, project_snapshot_envelope
from .render import explain_lines, summary_lines
from .core.event_types import ObservedEvent
from .core.event_store import EventStore
from .core.projection_index import ProjectionIndex
from .core.signal_engine import SignalEngine

# Global instances (single writer context)
_event_store = EventStore()
_projection_index = ProjectionIndex()
_signal_engine = SignalEngine()


def create_app() -> FastAPI:
    app = FastAPI(title="DBL Observer UI Server")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def root() -> dict[str, object]:
        return {
            "status": "ok",
            "service": "dbl-observer-server",
            "endpoints": [
                "GET /healthz",
                "POST /project",
                "POST /explain",
                "POST /summary",
                "GET /tail?stream_id=default&since=0",
                "GET /status",
                "GET /threads",
                "GET /threads/{thread_id}",
                "GET /signals",
                "POST /ingest",
                "GET /ui",
            ],
        }

    @app.get("/ui", response_class=HTMLResponse)
    def ui() -> HTMLResponse:
        base_dir = Path(__file__).parent
        ui_path = base_dir / "ui.html"
        return HTMLResponse(ui_path.read_text(encoding="utf-8"))

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/project")
    def project(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        if body.get("version") != "ui.v1.project":
            raise HTTPException(status_code=400, detail="invalid version")
        items = body.get("items")
        if not isinstance(items, list):
            raise HTTPException(status_code=400, detail="items must be list")
        try:
            events = project_raw_items(items)
        except ValueError as exc:
            return _error_response("invalid_input", str(exc))
        return {
            "version": "ui.v1.trace",
            "items": [_event_to_dict(event) for event in events],
        }

    @app.post("/explain")
    def explain(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        if body.get("version") != "ui.v1.trace":
            raise HTTPException(status_code=400, detail="invalid version")
        items = body.get("items")
        if not isinstance(items, list):
            raise HTTPException(status_code=400, detail="items must be list")
        try:
            events = parse_trace_items(items)
        except ValueError as exc:
            return _error_response("invalid_input", str(exc))
        lines = explain_lines(events, [])
        return {"version": "ui.v1.explain", "lines": list(lines)}

    @app.post("/summary")
    def summary(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        if body.get("version") != "ui.v1.trace":
            raise HTTPException(status_code=400, detail="invalid version")
        items = body.get("items")
        if not isinstance(items, list):
            raise HTTPException(status_code=400, detail="items must be list")
        try:
            events = parse_trace_items(items)
        except ValueError as exc:
            return _error_response("invalid_input", str(exc))
        lines = summary_lines(events)
        return {"version": "ui.v1.summary", "lines": list(lines)}

    @app.get("/tail")
    def tail(
        stream_id: str = Query("default"),
        since: int = Query(0, ge=0),
    ) -> dict[str, Any]:
        base_url = os.getenv("OBSERVER_GATEWAY_BASE_URL", "http://127.0.0.1:8010").strip()
        if base_url == "":
            raise HTTPException(status_code=400, detail="OBSERVER_GATEWAY_BASE_URL is empty")
        snapshot = _fetch_gateway_snapshot(base_url, stream_id, since)
        try:
            events = project_snapshot_envelope(snapshot)
        except ValueError as exc:
            return _error_response("invalid_input", str(exc))
        items = [_event_to_dict(event) for event in events]
        next_cursor = since
        if items:
            last = items[-1].get("event_id")
            if isinstance(last, int):
                next_cursor = last + 1
        return {"version": "ui.v1.tail", "items": items, "next_cursor": next_cursor}

    # --- Observability Endpoints (v1) ---

    @app.get("/status")
    def status() -> dict[str, Any]:
        """System-level metrics snapshot."""
        metrics = _projection_index.get_system_metrics()
        signals = _signal_engine.evaluate(_projection_index)
        signal_counts = {"info": 0, "warn": 0, "critical": 0}
        for s in signals:
            signal_counts[s.severity.value] += 1
        
        return {
            "observer_version": 1,
            "event_count": _event_store.count(),
            "last_index": _event_store.last_index(),
            "thread_count": metrics["thread_count"],
            "turn_count": metrics["turn_count"],
            "deny_rate": metrics["deny_rate"],
            "latency_ms": metrics["latency"],
            "active_signals": signal_counts,
        }

    @app.get("/threads")
    def list_threads() -> dict[str, Any]:
        """List all thread summaries."""
        threads = _projection_index.list_threads()
        return {
            "observer_version": 1,
            "threads": [
                {
                    "thread_id": t.thread_id,
                    "turns_total": t.turns_total,
                    "deny_total": t.deny_total,
                    "allow_total": t.allow_total,
                    "execution_error_total": t.execution_error_total,
                    "first_index": t.first_index,
                    "last_index": t.last_index,
                }
                for t in threads
            ],
        }

    @app.get("/threads/{thread_id}")
    def get_thread(thread_id: str) -> dict[str, Any]:
        """Get single thread summary with its turns."""
        thread = _projection_index.get_thread(thread_id)
        if thread is None:
            raise HTTPException(status_code=404, detail="thread not found")
        turns = _projection_index.list_turns_for_thread(thread_id)
        return {
            "observer_version": 1,
            "thread": {
                "thread_id": thread.thread_id,
                "turns_total": thread.turns_total,
                "deny_total": thread.deny_total,
                "allow_total": thread.allow_total,
                "execution_error_total": thread.execution_error_total,
                "first_index": thread.first_index,
                "last_index": thread.last_index,
            },
            "turns": [
                {
                    "turn_id": t.turn_id,
                    "parent_turn_id": t.parent_turn_id,
                    "decision_result": t.decision_result,
                    "reason_codes": t.reason_codes,
                    "latency_ms": t.latency_ms,
                    "has_execution": t.has_execution,
                    "has_errors": t.has_errors,
                    "first_index": t.first_index,
                    "last_index": t.last_index,
                }
                for t in turns
            ],
        }

    @app.get("/signals")
    def list_signals() -> dict[str, Any]:
        """List current active signals (NON_NORMATIVE attention markers)."""
        signals = _signal_engine.evaluate(_projection_index)
        return {
            "observer_version": 1,
            "signals": [
                {
                    "id": s.id,
                    "severity": s.severity.value,
                    "scope": s.scope,
                    "key": s.key,
                    "title": s.title,
                    "detail": s.detail,
                    "at_index": s.at_index,
                    "evidence": s.evidence,
                }
                for s in signals
            ],
        }

    @app.post("/ingest")
    def ingest(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        """Ingest gateway events into the observer store.
        
        Accepts {"events": [...]} from gateway snapshot format.
        Events are converted to ObservedEvent, stored, and projected.
        
        INVARIANT: Events must be ingested in gateway index order.
        No reordering is performed. ProjectionIndex expects monotonically
        increasing indices for correct aggregation.
        """
        events = body.get("events")
        if not isinstance(events, list):
            raise HTTPException(status_code=400, detail="events must be list")
        
        ingested = 0
        for raw in events:
            if not isinstance(raw, dict):
                continue
            observed = ObservedEvent.from_gateway_event(raw)
            _event_store.append(observed)
            _projection_index.feed(observed)
            ingested += 1
        
        return {"observer_version": 1, "ingested": ingested, "total": _event_store.count()}

    return app


def _event_to_dict(event) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "source": event.source,
        "artifact": event.artifact,
        "payload": event.payload,
        "canon_len": event.canon_len,
        "digest": event.digest,
        "diagnostics": list(event.diagnostics),
    }


def _error_response(code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"version": "ui.v1.error", "error": {"code": code, "message": message}},
    )


def _fetch_gateway_snapshot(base_url: str, stream_id: str, offset: int) -> dict[str, Any]:
    import urllib.parse
    import urllib.request

    params = {"offset": str(offset), "limit": "200", "stream_id": stream_id}
    url = base_url.rstrip("/") + "/snapshot?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(prog="dbl-observer-server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8020)
    args = parser.parse_args()

    uvicorn.run(create_app(), host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
