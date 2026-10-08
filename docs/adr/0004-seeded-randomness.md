# ADR-004 — Named seeded randomness

- Status: proposed scheme; implemented and worker-tested, reproducibility is a constraint
- Date: 2026-10-08
- Scope: simulation RNG ownership and supported replay envelope
- Decision owner and review activity: AE-003 Codex worker, author self-review;
  paired experiments AE-015, restoration AE-031
- Related assumption IDs and superseded ADR: MA-14; none superseded

## Context and uncertainty

A global RNG couples unrelated rules through draw count. Named streams reduce
that coupling but cannot by themselves align endogenous events across strategies.
Neither an RNG seed nor a toy run empirically calibrates a model.

## Alternatives and criteria

One global stream is smallest but fails unrelated-draw isolation. Named streams
are sufficient for this engineering fixture. Per-entity/per-exposure keyed draws
may better preserve paired workloads later. A portable custom PRNG adds code
without a current cross-runtime replay requirement.

## Decision and consequences

`NamedRandomness` requires an explicit integer root seed (signed, excluding bool)
and caches a `random.Random` instance per exact nonblank case-sensitive name.
Scheme **`sha256-json-name-mt19937-v1`** derives each seed from SHA-256 of UTF-8
JSON `[scheme, root_seed, name]`, ASCII escaped with separators `(',', ':')`.
Interpret the digest as an unsigned big-endian integer and initialize Python's
MT19937 with it. No `hash()`, ambient RNG, time, entropy or stream-creation index
enters derivation. Callers own stream names and draw methods/order and must not
reseed or replace stream state.

Replay is supported within CPython **3.12.13** and the pinned source/dependency
versions. The run manifest records scheme, streams, seeds and source hashes.
Python `randrange` and other distribution algorithms are part of this envelope.
An extra draw in `actor/policy` leaves `world/workload` unchanged; an extra draw in
`world/workload` shifts its later values. Later paired experiments must precompute
fixed exogenous samples or choose stable exposure keys before comparing strategies.

## Evidence and validation

[Tests](../../tests/unit/test_event_history.py) exercise repeat/different seeds,
stream isolation and process hash seeds. [Results](../../research/experiments/AE-003/results.json)
retain the measured same-stream shift counterexample alongside all seeds (17, 23).
This supports deterministic engineering behavior only; statistical independence,
cross-runtime portability and counterfactual alignment are not proven.

## Revisit trigger

AE-015 if changed strategy event counts misalign world samples; any change to
seed derivation, draw methods, names or runtime requires a new supported replay
version and fresh evidence. AE-031 must restore every used stream's state.
