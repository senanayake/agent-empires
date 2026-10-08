# ADR-003 — Integer discrete-event time

- Status: proposed; implemented and worker-tested in AE-003, no architecture gate
- Date: 2026-10-08
- Scope: simulation clock and pending command order
- Decision owner and review activity: AE-003 Codex worker, author self-review;
  composition AE-007, queue budgets AE-033
- Related assumption IDs and superseded ADR: MA-14, MA-15; none superseded

## Context and uncertainty

Python time authority is a product constraint. Reproducible event ordering is an
engineering hypothesis; a tick has no wall-time unit until a scenario defines it.
Pending work, executed commands and recorded facts are distinct.

## Alternatives and criteria

Integer discrete events avoid idle simulation work and floating-point ties.
Fixed steps could simplify a later continuous mechanic but add unnecessary idle
iterations here. Renderer/wall-time rules violate Python authority. A callback
scheduler complicates persistence before an application dispatch API is needed.

## Decision and consequences

`SimulationClock` queues immutable command-ID records using
`(tick, priority, insertion_seq)`; lower priorities run first. Sequence begins at
zero and increments only on successful scheduling. Command IDs do not break ties.
`pop_next()` removes one item and moves time to its tick; an empty queue does
nothing. `advance_to()` moves idle time but cannot pass the earliest queued tick.
Nonnegative Python integers are required; booleans/floats and past time fail.

New work may use the current tick. Its priority applies to the remaining queue,
never retroactively to already executed work. The caller dispatches command IDs
and emits facts at `clock.now`. There are no callbacks, automatic sleep, command
deduplication, concurrency, tick duration, cancellation or queue budget in AE-003.

## Evidence and validation

[Clock tests](../../tests/unit/test_clock.py) cover ties, dynamic same-time work,
idle advancement, invalid scheduling with no sequence consumption and a 150-item
sorted-reference invariant. [Replay results](../../research/experiments/AE-003/results.json)
show split advancement preserving histories. [Red/green evidence and review](../../research/experiments/AE-003/review.md)
bound the result to the fixture and CPython 3.12.13. No rendering-cadence proof exists.

## Revisit trigger

AE-007 if composition cannot preserve command/fact order; AE-022 for rendering
independence; AE-033 if same-tick rescheduling or queue growth requires budgets.
Save/resume must capture time, pending work and insertion cursor in AE-031.
