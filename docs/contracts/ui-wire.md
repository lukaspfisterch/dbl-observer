# UI Wire Contract (v1)

## Purpose
Define the observer UI wire protocol for dbl-observer.

Status: normative (tested)

## Versions
- trace: "ui.v1.trace"
- explain: "ui.v1.explain"
- summary: "ui.v1.summary"
- error: "ui.v1.error"
- project: "ui.v1.project"
- tail: "ui.v1.tail"

## ObservationTrace (ui.v1.trace)
```json
{
  "version": "ui.v1.trace",
  "items": [
    {
      "event_id": 1,
      "source": "adapter",
      "artifact": "record",
      "payload": {},
      "canon_len": 2,
      "digest": "sha256:<hex>",
      "diagnostics": []
    }
  ]
}
```

## ExplainOutput (ui.v1.explain)
```json
{
  "version": "ui.v1.explain",
  "lines": [
    "event_id=1 source=adapter artifact=record canon_len=2 digest=sha256:... diagnostics=[]"
  ]
}
```

## SummaryOutput (ui.v1.summary)
```json
{
  "version": "ui.v1.summary",
  "lines": [
    "total_events=1",
    "source=adapter count=1",
    "artifact=record count=1"
  ]
}
```

## ErrorOutput (ui.v1.error)
```json
{
  "version": "ui.v1.error",
  "error": {
    "code": "invalid_input",
    "message": "details"
  }
}
```

## ProjectInput (ui.v1.project)
Raw items for project mode.
```json
{
  "version": "ui.v1.project",
  "items": [
    {
      "event_id": 1,
      "source": "adapter",
      "artifact": "record",
      "payload": {}
    }
  ]
}
```

## TailOutput (ui.v1.tail)
```json
{
  "version": "ui.v1.tail",
  "items": [ { "event_id": 1, "source": "adapter", "artifact": "record", "payload": {}, "canon_len": 2, "digest": "sha256:<hex>", "diagnostics": [] } ],
  "next_cursor": 2
}
```

## Determinism
- ObservationTrace items are in deterministic order.
- Explain output is deterministic for the same trace.
- Summary output is deterministic for the same trace.

## Notes
- UI must treat items and lines as opaque data.
- No DBL event kinds appear in this contract.
