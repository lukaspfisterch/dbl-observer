# dbl-observer

## Purpose
dbl-observer is an **observation-only visibility layer** over existing KL/DBL artifacts.
It projects artifacts into a unified observation trace for deterministic replay visibility
and diagnostics without introducing normativity or execution.

---

## Non-goals
- No decisions or validation
- No governance logic
- No execution side effects
- No reinterpretation of KL or DBL semantics

---

## What it does
- Reads existing artifacts via source adapters
- Projects them into a unified observation trace
- Computes deterministic canonicalization and digests
- Emits observation-only diagnostics and renderings
- **Aggregates events into projections** (Thread, Turn, Actor, Policy summaries)
- **Generates NON_NORMATIVE signals** (attention markers, not decisions)

---

## Contracts
Contracts are the primary API:
- `docs/contracts/wire.md`
- `docs/contracts/canonicalization.md`
- `docs/contracts/digest.md`
- `docs/contracts/diagnostics.md`
- `docs/contracts/cli.md`

---

## CLI
`dbl-observer` supports:
- `project`: raw artifact input -> observation trace
- `diagnostic`: validate and annotate an observation trace
- `explain`: human-readable rendering
- `diff`: comparison against a reference trace
- `summary`: trace summary counts
- `gateway`: read dbl-gateway snapshot and render observation-only lines

**Gateway quick start:**
```powershell
dbl-observer --mode gateway
dbl-observer --mode gateway --follow
dbl-observer --mode gateway --gateway-url http://127.0.0.1:8010 --limit 50
```

---

## Observer Server

The observer includes an HTTP server with REST API endpoints.

**Start the server:**
```powershell
$env:OBSERVER_GATEWAY_BASE_URL="http://127.0.0.1:8010"
dbl-observer-server --host 127.0.0.1 --port 8020
```

**URLs:**
| Endpoint | Description |
|----------|-------------|
| `GET /` | Endpoint list |
| `GET /docs` | Swagger UI (interactive API docs) |
| `GET /healthz` | Health check |
| `GET /status` | System metrics (event count, deny rate, latency P50/P95/P99) |
| `GET /threads` | List of thread summaries |
| `GET /threads/{id}` | Single thread with turn details |
| `GET /signals` | Active attention markers (NON_NORMATIVE) |
| `POST /ingest` | Ingest gateway events into projection engine |
| `GET /tail` | Fetch events from gateway |
| `POST /project` | Project raw items to trace |
| `POST /explain` | Render trace as human-readable lines |
| `POST /summary` | Summarize trace counts |

**Example: Ingest events from gateway**
```powershell
$snapshot = Invoke-RestMethod -Uri "http://localhost:8010/snapshot?limit=200"
Invoke-RestMethod -Uri "http://localhost:8020/ingest" -Method POST -Body ($snapshot | ConvertTo-Json -Depth 10) -ContentType "application/json"
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

Signals are **NON_NORMATIVE**: they are descriptive observations, not decisions.

---

## Tests
- Determinism and replay visibility
- Observational non-interference
- Strict contract adherence
- Projection index correctness
- Signal engine purity (same input → same output)

Run all tests:
```powershell
python -m pytest tests/ -v
```
