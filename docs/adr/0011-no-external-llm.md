# ADR-011 — MVP has no external LLM runtime dependency

- Status: accepted as existing product constraint; packaged offline proof pending
- Date: 2026-10-09
- Scope: system
- Decision owner and review activity: user brief/campaign; AE-020 worker self-review
- Related assumption IDs and superseded ADR: MA-05/14; none

## Context and uncertainty

The campaign requires independently reusable Python rules and seeded replay without
an API key. Toy finite Actor policies do not establish real human/LLM performance.

## Alternatives and criteria

External LLM actor control adds live input, cost and reproducibility boundaries.
Deterministic finite policies and seeded domain randomness already serve the bounded
MVP. A separately recorded optional LLM adapter remains a post-MVP possibility.

## Decision and consequences

Keep the MVP runtime free of external LLM dependencies/services. Transport consumes
application services; simulation imports only selected standard-library/domain
modules. Actor kind remains distinct from profile, authority and evidence. There
is no LLM request in commands/endpoints and no cloud component. This records the
product constraint; it does not validate model realism.

## Evidence and validation

[Campaign architecture](../mvp-campaign.md#7-major-technical-architecture), unchanged
empty runtime dependencies in `pyproject.toml`, and the AE-020 import-boundary test
support the current source boundary. [Review](../../research/experiments/AE-020/review.md)
records local tests and limits. Offline packaged launch is still AE-032, not proven
by source inspection or the sandbox's blocked loopback attempt.

## Revisit trigger

An explicit post-MVP requirement for LLM actors must introduce a separately reviewed
adapter, recorded inputs and narrower reproducibility claims; never silently add
a runtime service to domain code.
