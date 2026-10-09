# AE-005 channels and scoped handoff

Disposition: pass for the bounded mechanism, by the assigned AE-005 Codex worker
(author self-review). No independent domain reviewer, architecture acceptance,
human participant, calibration, integration or publication claim.

## Predecessor review

Entry `36b26e135671fe8fc20eda63c1f2f602fbcc4148` contains AE-004's actual committed
holdings implementation. Its receipt, 41 tests and read-only fixture replay passed
([entry-checks.json](entry-checks.json)). Reviewed code, tests, fixture/results,
review and operator recovery note: historical worker Git failure was preserved,
and actual artifacts are now in this checkout. The access/source limitations fit
AE-005. No gate or architecture acceptance was inferred.

Only MA-04 changes in the shared assumptions register. The
[archived entry register](predecessor-model-assumptions.md) preserves AE-004's
bound bytes; its other bindings remain unchanged. Its post-edit hash failure is
expected and retained in `predecessor-binding-review.json`, not repaired by
rewriting the predecessor receipt. ADRs and shared handoff ledger are outside the
allowed paths; this scoped ledger records the handoff. Existing Python/time/RNG/
history constraints are applied without a new dependency or architecture decision.

## Rules and trace

- A directed edge connects two present actors. Send reads a fresh sender view;
  personally held or explicitly readable artifact content can be sent. Catalog
  entries, private documents, teammates and source labels grant no sending access.
- One message consumes one admission in its edge's current integer tick. There
  is no buffer: overflow is rejected without a charge, draw or scheduled work.
  Capacity resets each tick, independently per edge. Positive latency permits
  pipelining; it is not a limit on total in-flight messages.
- Connection and send costs are nonnegative integer toy resource units. Accepted
  sends cost even if lost. No budget enforcement or ongoing maintenance exists.
- The caller pops AE-003 clock work and dispatches each transfer at its arrival
  tick. Sending snapshots the holding; later sender departure/access revocation
  does not recall it. A departed recipient causes `InformationLost` at arrival.
- Loss and distortion use separate named RNG streams keyed by send command ID.
  Both draws are sampled for a present recipient, including boundary probabilities.
  Loss excludes distortion/delivery. World draws and actor kinds do not affect
  these samples. Reusing a send command ID is rejected.
- Distortion applies a configured exact topic/proposition replacement. Unsupported
  propositions are rejected at admission when distortion probability is positive.
  A distorted claim gets a distinct item ID; no existing source item is rewritten.
  Source IDs, confidence, freshness and explicitness survive unchanged. High trust
  cannot improve reliability, confer authority or turn copies into evidence.

Successful trace: acquisition → `TransferSent` → `KnowledgeHoldingRecorded` →
optional `InformationDistorted` → `KnowledgeTransferred`. All receipt facts share
the arrival tick. The holding record cites the send; the transfer outcome cites
the send, acquisition and distortion fact. Send cites the actual current holding
record/access revision and channel connection. Recorded item/source references
permit provenance inspection without granting an actor lookup into the audit.
Forwarding is another explicit send and another delay/cost, never a graph flood.

The owner is trusted, single-consumer and shares the store's history and clock.
The `communication:` namespace for generated items, holdings and queue commands
is reserved. This uses AE-004's public view and event history without reading its
private catalog. Same-owner composition, proper clock dispatch and reserved IDs
are caller contracts; arbitrary hostile mutation, concurrent owners, persistence
and cross-owner transactions are unproven. Direct artifact destinations, channel
removal, retries, automatic discovery/routing and correlated outages are absent.

## Evidence and counterexamples

[Protocol](protocol.md) predates tests/implementation. The initial
[red](tdd-red.json) is a real missing-module collection failure; the first
[green](tdd-green.json) passed 35 tests. Review then found an incorrect causal
parent: a repeated send cited the prior send mentioning the source instead of its
acquisition. [Assertion red](lineage-red.json) records 1 failed/38 passed; the
[fix](lineage-green.json) passes all 39 focused cases. Other cases cover invalid
parameters/parents/IDs, no-charge rejection, departures, immutable snapshots,
external clock work, inaccessible artifacts and copied-source invariants.

The experiment's first authoring command had a missing bracket and failed before
any output files were authored; [failure](experiment-author.json) is retained.
[Successful authoring](experiment-author-green.json) records the corrected runner.
[Results](results.json) retain every seed 0–31, per-message draws/outcomes and
canonical-history hashes. [Traces](traces.json) retain each profile's seed 0 and
all four topology histories. The [manifest](run-manifest.json) binds source,
initial state, ordered commands, runtime, units, ranges and invented parameters.

Each profile attempts 128 messages (32 seeds × 4), costs 128 units and resolves at
tick 2. Distorted messages are a subset of delivered messages, not extra outcomes.

| Loss / distortion probability | Delivered | Lost | Distorted | Delivered per seed: mean [min, max] |
| --- | ---: | ---: | ---: | --- |
| 0 / 0 | 128 | 0 | 0 | 4 [4, 4] |
| 1 / 0 | 0 | 128 | 0 | 0 [0, 0] |
| 0 / 1 | 128 | 0 | 128 | 4 [4, 4] |
| 0.25 / 0.5 | 94 | 34 | 49 | 2.9375 [1, 4] |
| 0.75 / 0.5 | 23 | 105 | 13 | 0.71875 [0, 3] |

No tested seed violates the invariants. Lost-message seeds remain in the results;
they are valid negative outcomes. Paired samples ensure higher loss cannot rescue
a message in this model. Repeated runs and reversed roster registration with
all-agent relabeling produce identical canonical traces within CPython 3.12.13.
Verification regenerates temporary artifacts and compares without overwriting.

| Topology / route | Recipient access | Arrival | Total cost |
| --- | --- | ---: | ---: |
| Isolated | No | — | 0 |
| Direct fast edge | Yes | 1 | 10 |
| Two-hop cheap route | Yes | 4 | 4 |
| Both routes, use direct | Yes | 1 | 12 |

The direct edge satisfies an invented deadline 1/budget 10 constraint; the chain
satisfies deadline 4/budget 4. Neither satisfies the other's constraint. The union
is dominated on this workload because unused connections still cost. Isolation
is cheapest but transfers nothing. These are inspectable authored trade-offs,
not proof that no graph dominates across all parameterizations or workloads.
With zero connection cost extra unused links are free; no universal anti-density
rule is claimed. Reliability statistics assume independent draws; correlated
failure, scale, comprehension and enjoyment remain untested.

## Scoped ledger

| Activity | Repository disposition | Controller disposition |
| --- | --- | --- |
| AE-005 | Communication mechanism, 39 focused/124 total passing tests, reproduced seeded/topology evidence and MA-04 complete; local commit blocked by read-only Git metadata. | Independent validation, delivery recovery and any local integration remain controller-owned. |

Recommend AE-006 only after completed local delivery and controller review/
validation. No successor, push, target integration or campaign completion was
executed or asserted.

The single permitted `git add` attempt returned exit 128: Git could not create
the worktree's `index.lock` on its read-only shared metadata mount.
[delivery.json](delivery.json) retains the exact error. No retry or commit was
attempted after that failure; no worker commit exists. Completed source and
validation evidence remain for operator/controller recovery. The launch-specific
delivery rule requires worker status `failed`, despite the mechanism receipt's
bounded pass. No successor is recommended until local delivery is recovered.

## Causal review correction

The [operator review](operator-review.md) adds three regression cases. Sends retain
completed acquisition and current access as distinct parents; forwarded distortion
and restored access remain traceable. Recipient-unavailable loss cites departure.
The 160-case results and topology costs/timings are unchanged.
