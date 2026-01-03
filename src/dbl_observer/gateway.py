from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from typing import Any, Iterable, Optional


def observe_gateway(
    *,
    base_url: str,
    stream_id: str,
    lane: Optional[str],
    limit: int,
    follow: bool,
    poll_interval: float,
) -> Iterable[dict[str, Any]]:
    offset = 0
    while True:
        events, meta = _fetch_snapshot(
            base_url=base_url,
            stream_id=stream_id,
            lane=lane,
            offset=offset,
            limit=limit,
        )
        for event in events:
            yield event
        offset = offset + len(events)
        if not follow:
            break
        if not events:
            time.sleep(poll_interval)


def render_gateway_event(event: dict[str, Any], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(event, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    index = _get_int(event, "index")
    kind = _get_str(event, "kind")
    lane = _get_str(event, "lane")
    actor = _get_str(event, "actor")
    intent_type = _get_str(event, "intent_type")
    stream_id = _get_str(event, "stream_id")
    correlation_id = _get_str(event, "correlation_id")
    digest = _get_str(event, "digest")
    payload = event.get("payload")
    payload_json = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return (
        f"index={index} kind={kind} lane={lane} actor={actor} "
        f"intent_type={intent_type} stream_id={stream_id} correlation_id={correlation_id} "
        f"digest={digest} payload={payload_json}"
    )


def _fetch_snapshot(
    *,
    base_url: str,
    stream_id: str,
    lane: Optional[str],
    offset: int,
    limit: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    params: dict[str, str] = {
        "offset": str(offset),
        "limit": str(limit),
        "stream_id": stream_id,
    }
    if lane:
        params["lane"] = lane
    url = base_url.rstrip("/") + "/snapshot?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if isinstance(data, list):
        return data, {"offset": offset, "limit": limit}
    if isinstance(data, dict) and isinstance(data.get("events"), list):
        meta = {
            "length": data.get("length"),
            "offset": data.get("offset"),
            "limit": data.get("limit"),
            "v_digest": data.get("v_digest"),
        }
        return data["events"], meta
    raise ValueError("snapshot response is not a list or envelope")


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
