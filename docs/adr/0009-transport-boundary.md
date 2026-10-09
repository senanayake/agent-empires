# ADR-009 — Passive local HTTP boundary

- Status: proposed, implemented bounded spike; local runtime budget observed; Godot fit pending
- Date: 2026-10-09
- Scope: component — passive presentation transport
- Decision owner and review activity: AE-020 worker self-review; AE-021/022 revisit
- Related assumption IDs and superseded ADR: MA-14/15; none

## Context and uncertainty

Python authority is an existing constraint. The owner brought the passive window
forward after AE-016; management gates remain outstanding. A real work/history
slice needs commands, reconnect state and contiguous events without exposing the
private world. Godot consumption and actual loopback latency remain unmeasured.

## Alternatives and criteria

JSONL process I/O offers small framing but requires owned bidirectional pipes.
Loopback HTTP offers explicit independent requests/reconnect at the cost of a
listener/process lifecycle. Streaming/frameworks add machinery without an observed
need. Criteria are strict version/ID/rejection semantics, private-state projection,
replaceability, no domain dependency on I/O, and provisional acknowledgment p95
below 250 ms on recorded hardware. The budget is not empirical usability evidence.

## Decision and consequences

Implement one standard-library sequential loopback HTTP adapter. Application owns
commands/deduplication/public projections; adapter owns HTTP framing. The
[contract](../transport-contract.md) defines pause/step/disconnect/cursor behavior.
No dependency or architecture acceptance is implied. The finite preview cache and
sequential request handling are deliberate bounded choices, not general-service
capacity claims. No second adapter is benchmarked without a demonstrated failure.

## Evidence and validation

[AE-020 review](../../research/experiments/AE-020/review.md) and focused contracts
exercise real serialized HTTP handling and domain invariants. The
[measurement](../../research/experiments/AE-020/measurement.json) retains the socket
permission failure. Handler-only p95 is 0.403191 ms on the recorded i7-14700F,
excluding actual network/process costs. HTTP's budget and Godot fit are pending
controller/runtime evidence; no comparative JSONL result or human acceptance.

## Revisit trigger

Real loopback p95 at/above 250 ms, AE-021 client/process difficulty, AE-022 frame
independence/reconnect failure, or AE-033 session backlog/cache exhaustion. First
reproduce the failure; compare JSONL only when that failure justifies another adapter.

Independent operator validation measured real separate-process p95 0.490115 ms
on this host and passed 37 transport/524 full-suite tests; see the
[operator measurement](../../research/experiments/AE-020/operator-loopback-measurement.json).
The old unavailable worker result is preserved. HTTP remains provisional until
the Godot client/frame/reconnect experiments; no low-end hardware claim.
