# dbl-observer

**Observation-only visibility layer** over DBL gateway events.
No decisions. No governance. Just deterministic insight.

---

## Quick Start: Maximum Impact in 3 Commands

### 1. Start Observer (ingest gateway events)
```powershell
# Terminal 1: Start server
$env:OBSERVER_GATEWAY_BASE_URL="http://127.0.0.1:8010"
dbl-observer-server --port 8020

# Terminal 2: Ingest current gateway state
$snapshot = Invoke-RestMethod -Uri "http://localhost:8010/snapshot?limit=500"
Invoke-RestMethod -Uri "http://localhost:8020/ingest" -Method POST -Body ($snapshot | ConvertTo-Json -Depth 10) -ContentType "application/json"
```

### 2. System Health Check
```powershell
# What's the system state?
curl http://localhost:8020/status
```
```json
{
  "event_count": 66,
  "thread_count": 6,
  "turn_count": 22,
  "deny_rate": 0.0,
  "active_signals": { "info": 0, "warn": 0, "critical": 0 }
}
```

### 3. Thread Deep-Dive
```powershell
# List all threads
curl http://localhost:8020/threads

# Pick a thread ID from the list, then:
curl http://localhost:8020/threads/{thread_id}
```
```json
{
  "thread": { "turns_total": 6, "deny_total": 0, "allow_total": 6 },
  "turns": [
    { "turn_id": "...", "decision_result": "ALLOW", "has_execution": true },
    { "turn_id": "...", "parent_turn_id": "...", "decision_result": "ALLOW" }
  ]
}
```

> **Note:** Thread IDs are UUIDs, not "default". Use `/threads` first to discover available thread IDs.

---

## High-Impact Commands (Ranked)

| Command | What it tells you | When to use |
|---------|-------------------|-------------|
| `GET /status` | System pulse (events, deny rate, signals) | First look |
| `GET /threads` | All conversations, sorted by recency | Find active work |
| `GET /threads/{id}` | Turn-by-turn breakdown of one thread | Drill into specifics |
| `GET /signals` | Automated attention markers | "What needs my attention?" |

For CLI-based analysis (via `dbl-operator`):

| Command | What it tells you |
|---------|-------------------|
| `dbl-operator failures` | Execution errors vs policy denials |
| `dbl-operator integrity` | Protocol completeness (structural trust) |
| `dbl-operator latency` | P50/P95/P99 across phases |

---

## Purpose

dbl-observer is an **observation-only visibility layer** over existing DBL artifacts.
It projects artifacts into a unified observation trace for deterministic replay visibility
and diagnostics without introducing normativity or execution.

### Non-goals
- No decisions or validation
- No governance logic
- No execution side effects
- No reinterpretation of DBL semantics

### What it does
- Reads gateway events via source adapters
- Projects them into a unified observation trace
- Computes deterministic canonicalization and digests
- **Aggregates events into projections** (Thread, Turn, Actor, Policy)
- **Generates NON_NORMATIVE signals** (attention markers, not decisions)

---

## Observer Server

### Full Endpoint Reference

| Endpoint | Description |
|----------|-------------|
| `GET /` | Endpoint list |
| `GET /docs` | Swagger UI (interactive API docs) |
| `GET /healthz` | Health check |
| `GET /status` | System metrics |
| `GET /threads` | List thread summaries |
| `GET /threads/{id}` | Single thread with turns |
| `GET /signals` | Active attention markers |
| `POST /ingest` | Ingest gateway events |
| `GET /tail` | Fetch events from gateway |

### Start the Server
```powershell
pip install -e .
$env:OBSERVER_GATEWAY_BASE_URL="http://127.0.0.1:8010"
dbl-observer-server --port 8020
```

### Ingest Workflow
```powershell
# Fetch from gateway and push to observer
$snapshot = Invoke-RestMethod -Uri "http://localhost:8010/snapshot?limit=500"
Invoke-RestMethod -Uri "http://localhost:8020/ingest" -Method POST -Body ($snapshot | ConvertTo-Json -Depth 10) -ContentType "application/json"
```

**INVARIANT:** Events must be ingested in gateway index order. No reordering is performed.

---

## CLI Modes

`dbl-observer` CLI supports:
- `project`: raw artifact input → observation trace
- `diagnostic`: validate and annotate an observation trace
- `explain`: human-readable rendering
- `diff`: comparison against a reference trace
- `summary`: trace summary counts
- `gateway`: read dbl-gateway snapshot and render lines

```powershell
dbl-observer --mode gateway --follow
dbl-observer --mode gateway --limit 50
```

---

## Core Modules (v0.3.x)

### Projection Layer (`core/`)
- **ObservedEvent**: Stable schema for gateway events (1:1 mapping)
- **EventStore**: Thread-safe append-only store with indexed access
- **ProjectionIndex**: Incremental aggregation engine
  - `TurnSummary`: Per-turn state (decision, latency, execution)
  - `ThreadSummary`: Per-thread aggregates (deny/allow/error counts)
  - `ActorSummary`: Per-actor activity profile
  - `PolicyWindow`: Timeline of active policy versions
  - `LatencyProfile`: P50/P95/P99 from bounded sample window

### Signal Layer
- **SignalEngine**: Stateless, pure-function evaluator
  - `latency_p95_elevated` / `latency_p95_critical`
  - `deny_rate_elevated` / `deny_rate_critical`
  - `error_cluster`
  - `frequent_policy_changes`

Signals are **NON_NORMATIVE**: descriptive observations, not decisions.

---

## Contracts

Contracts are the primary API:
- `docs/contracts/wire.md`
- `docs/contracts/canonicalization.md`
- `docs/contracts/digest.md`
- `docs/contracts/diagnostics.md`
- `docs/contracts/cli.md`

---

## Tests

```powershell
python -m pytest tests/ -v
```

- Determinism and replay visibility
- Observational non-interference
- Strict contract adherence
- Projection index correctness
- Signal engine purity (same input → same output)
