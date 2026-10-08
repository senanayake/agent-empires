# ADR-005 — Append-only causal facts and command replay

- Status: proposed representation; implemented and worker-tested, history is a constraint
- Date: 2026-10-08
- Scope: in-memory fact envelope and canonical command-fixture replay
- Decision owner and review activity: AE-003 Codex worker, author self-review;
  composed facts AE-007/010, save/replay scope AE-031
- Related assumption IDs and superseded ADR: MA-06, MA-14; none superseded

## Context and uncertainty

AE-002 rejects rewriting old subjects and conflating supporting evidence with
direct cause. A recorded causal graph expresses modeled dependencies; it cannot
prove empirical causality or supply actor access to private audit information.

## Alternatives and criteria

A mutable debug log loses historical claims. Full event sourcing could reconstruct
state but needs reducers, migration and state-completeness proof. An immutable
fact history plus replay of ordered commands supplies the narrow requirement now.

## Decision and consequences

`EventHistory.append` validates before assigning an ID or changing storage. Facts
contain `{run_id}:event:{sequence}` IDs (zero-based), monotonic nonnegative ticks,
total sequence, type/schema version, entity/type/version refs, command and
correlation IDs, typed earlier parents and a JSON-object payload. The caller must
choose a stable run identity; IDs are unique within that history, not globally
generated UUIDs. Append order decides equal-time fact order.

Parents must already exist in the same history, making self/future/dangling
references and cycles impossible through append. Relations are `direct_cause`,
`supporting_evidence`, and `association`; duplicate identical links fail. Entity
existence, authority, access and cross-owner atomicity remain domain concerns.
Ticks record fact time; a later observation can carry earlier occurrence time in
its payload without inserting a fact into the past.

Envelopes/refs are frozen, returned histories are tuple snapshots, and payloads
are stored as immutable canonical bytes; access/export returns detached copies.
History schema 1 serializes sorted string-keyed maps, ordered arrays, ASCII-escaped
strings and finite JSON numbers with no whitespace/newline. Reject sets, custom
objects, non-string keys, cycles, NaN and Infinity. Float formatting and string
code points are preserved under the pinned runtime; no RFC 8785 or Unicode
normalization claim is made. Ordered entity/parent arrays are never sorted as sets.

The engineering fixture replays initial state plus ordered commands and root seed
through the same clock/history/RNG primitives. It writes canonical history files
and a source-hashed manifest. No application command API, durable append writer,
database, reducer, save/resume or schema migration is implemented.

## Evidence and validation

[Tests](../../tests/unit/test_event_history.py) exercise immutable nested payloads,
failed-append atomicity, DAG order, schema metadata, canonical encoding and
fresh-process replay. [Protocol and results](../../research/experiments/AE-003/protocol.md)
cover seeds 17/23 and controls. [Review](../../research/experiments/AE-003/review.md)
records limits and actual worker red/green output; no human or independent domain
acceptance is implied.

## Revisit trigger

AE-007/010 if composed events cannot express traceable dependencies or accessible
observations. AE-031 must prove restoration of queue, RNG state, command cursor
and domain state; replaying this four-command fixture does not establish that.
