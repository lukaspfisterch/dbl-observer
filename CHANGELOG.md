# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2026-01-19

### Added

#### Core Projection Layer (`core/`)
- **ObservedEvent**: Stable, minimal schema for gateway events (1:1 mapping from gateway payload). Separates internal processing from UI/render concerns.
- **EventStore**: Thread-safe, append-only in-memory store with indexed access by `thread_id`, `turn_id`, `actor`.
- **ProjectionIndex**: Incremental, deterministic aggregation engine producing:
  - `TurnSummary`: Per-turn state (decision result, latency, execution status)
  - `ThreadSummary`: Per-thread aggregates (deny count, allow count, error count)
  - `ActorSummary`: Per-actor activity profile
  - `PolicyWindow`: Timeline of effective policy versions
  - `LatencyProfile`: P50/P95/P99 from bounded sample window (5000 samples)

#### Signal Layer
- **SignalEngine**: Stateless, pure-function evaluator producing NON_NORMATIVE attention markers:
  - `latency_p95_elevated` / `latency_p95_critical`
  - `deny_rate_elevated` / `deny_rate_critical`
  - `error_cluster`
  - `frequent_policy_changes`
- Signals are descriptive observations, not decisions.

#### Server API Extensions
- `GET /status`: System-level metrics (event count, deny rate, latency quantiles, signal counts)
- `GET /threads`: List of all thread summaries
- `GET /threads/{thread_id}`: Single thread with its turn summaries
- `GET /signals`: Current active signals
- `POST /ingest`: Ingest gateway events into observer store and projection engine

### Changed
- Server now initializes global `EventStore`, `ProjectionIndex`, and `SignalEngine` instances.
- Root endpoint (`/`) now lists new observability endpoints.

### Notes
- All existing endpoints (`/tail`, `/project`, `/explain`, `/summary`) remain unchanged.
- All 24 existing tests continue to pass.
- 10 new tests added for projection and signal modules.
- Swagger UI available at `http://localhost:8020/docs` when server is running.

### Quickstart
```powershell
# Install
pip install -e .

# Start server
$env:OBSERVER_GATEWAY_BASE_URL="http://127.0.0.1:8010"
dbl-observer-server --port 8020

# Ingest events from gateway
$snapshot = Invoke-RestMethod -Uri "http://localhost:8010/snapshot?limit=200"
Invoke-RestMethod -Uri "http://localhost:8020/ingest" -Method POST -Body ($snapshot | ConvertTo-Json -Depth 10) -ContentType "application/json"

# View status
curl http://localhost:8020/status
```

## [0.3.2] - 2026-02-02

### Added
- `GET /ui`: Structured, filterable event viewer with collapsible payload sections.

### Fixed
- CLI gateway follow now exits cleanly on Ctrl+C.
