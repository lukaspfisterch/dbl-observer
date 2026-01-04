from __future__ import annotations

import json
import os
from typing import Any, Mapping

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .project import project_raw_items, parse_trace_items, project_snapshot_envelope
from .render import explain_lines, summary_lines


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
            ],
        }

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
