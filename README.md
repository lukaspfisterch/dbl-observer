# dbl-observer

## Purpose
dbl-observer is an observation-only visibility layer over existing KL/DBL artifacts.
It projects artifacts into a unified observation trace for deterministic replay visibility
and diagnostics without introducing normativity or execution.

## Non-goals
- No decisions or validation
- No governance logic
- No execution side effects
- No reinterpretation of KL or DBL semantics

## What it does
- Reads existing artifacts via source adapters
- Projects them into a unified observation trace
- Computes deterministic canonicalization and digests
- Emits observation-only diagnostics and renderings

## Contracts
Contracts are the primary API:
- docs/contracts/wire.md
- docs/contracts/canonicalization.md
- docs/contracts/digest.md
- docs/contracts/diagnostics.md
- docs/contracts/cli.md

## CLI
`dbl-observer` supports:
- `project`: raw artifact input -> observation trace
- `diagnostic`: validate and annotate an observation trace
- `explain`: human-readable rendering
- `diff`: comparison against a reference trace
- `summary`: trace summary counts
- `gateway`: read dbl-gateway snapshot and render observation-only lines

## Tests
- Determinism and replay visibility
- Observational non-interference
- Strict contract adherence
