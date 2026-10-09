# AE-010 worker self-review and scoped ledger

Disposition: pass for the bounded fictional payment mechanism. Reviewer: assigned
Codex worker self-review, with no independent domain reviewer or human participants.
Independent validation and local integration remain controller-owned.

AE-009's receipt passed before editing, and its actual delivery source, tests,
protocol, green-change artifact, negative findings and operator delivery recovery
were reviewed. Proposals pin decisions, executable retry plans and conformance;
they grant neither world fitness nor automatic shipping. No missing predecessor
blocks this packet. Updating MA-07/08 legitimately makes the predecessor's shared
register hash historical; its exact entry bytes are preserved in
predecessor-model-assumptions.md. No predecessor receipt was rewritten.

PaymentOutcomes takes the existing clock/history after delivery is quiescent.
Explicit ship validates the recorded proposal and all pinned justification fields
before scheduling exposure. World configuration and immutable per-operation draws
never inspect actor kind, replacement or certainty. Initial ambiguous failure can
hide execution: the scenario's duplicate_probability is interpreted as the chance
of that hidden commit, not a fixed incident chance. Stable keys acknowledge it;
new/absent keys create harm only on successful additional execution. Declines can
fail repeatedly, cost resources and terminate in abandonment; transient failures
can recover after readiness. Success/abandonment stops unused retries. Audit
coverage affects recorded coverage, not physical damage or monitoring detection.
Every incident in these experiments links the actual attempt, deployment,
idempotency decision and its predeployment gap fact. Gap links are associations,
not extra damage causes; known-risk choices need not invent an information gap.

The saved protocol preceded results. Named per-operation/ordinal draws hold
workloads fixed across six strategies and five controls, 16 seeds in each world.
The 357 cases include five explicit boundaries; 27 complete histories retain
seed-0 controls and boundaries, while all seeds retain raw per-payment outcomes,
workloads, commands, parameters, hashes and per-seed paired differences. No seed
was removed, and the original PaymentCo input remains unchanged.

| Paired soft retries versus blanket prohibition | World A | World B |
| --- | --- | --- |
| Mean abandoned payments per 24 eligible | 7.3125 versus 6.4375 | 6.75 versus 8.4375 |
| Mean additional retry resource cost | +8.0625 | +9.25 |
| Seeds with more abandonment | 1, 2, 4, 6, 7, 9, 10, 11, 12, 15 | 11 |
| Unsafe strategy's incident-free seeds | 3, 5, 6, 9, 11 | 0, 1, 2, 3, 5, 6, 7, 9, 11, 12, 15 |

These are conditional toy effects, not financial or organizational estimates.
Retries can increase completed payments while increasing abandonment in other
customers; report both. Repeated ordinal abandonment opportunities, independent
samples, fixed arrivals, perfect delayed monitoring and one readiness threshold
are invented mechanisms. Zero traffic has no incident and no defined goal rate.
The goal's target/window remain authored constraints; no fitness acceptance or
universal target attainability is inferred from these finite runs. The observation
stream retains old deployment versions but does not enact learning/policy revision.

Actual failures are retained: missing-module collection red; workload dataclass
serialization failure and its focused red; a monitoring control that incorrectly
compared event IDs; and provenance accepting unrelated/postdeployment gaps.
The monitoring comparison now ignores only sequence-dependent result event IDs,
checking every other payment field and all metrics. Histories still differ where
feedback interleaves, as expected. before-monitoring-review and
before-provenance-review contain losslessly compressed raw runs/traces and exact
source snapshots. Both comparison and provenance regressions have red/green
receipts. No world parameter or physical rule was tuned after reading results.

Final validation: 35 focused tests, 295 total tests, canonical runs/traces replay,
and fresh timing approximately four seconds against 60 seconds pass. CLI tests
also exercise overwrite refusal, tampered-evidence rejection, and a fresh timing
budget failure. CPython 3.12.13 and checkout-local locked dependencies were used.
Source review confirms simulation imports only standard library and simulation
modules. Existing ADRs apply; no dependency, context boundary or accepted
architecture decision changed. No participant, usability, calibration, deployment
outside the toy world, integration, publication or campaign-completion claim.

| Activity | Repository disposition | Controller disposition |
| --- | --- | --- |
| AE-010 | Outcomes, tests, paired experiment, negative findings, assumption updates and bound self-reviewed receipt complete. Local Git delivery is reported separately, with its actual error retained if it fails. | Independent command validation and integration belong to the controller. |

AE-011 is the bounded successor only after local delivery and controller validation;
it requires actual participant records. No successor has been executed or launched.

Required local delivery failed: the single staging attempt exited 128 because
shared Git metadata could not create index.lock on a read-only filesystem.
delivery.json retains the exact command/error. No commit, retry or push occurred;
operator hash-reviewed recovery is required before recommending a successor.
The optional new-file whitespace runner initially misread --no-index exit 1;
raw output and actual clean/dirty fixture diagnostics are retained in
new-file-whitespace*.json. No whitespace errors or required-check failures exist.

## Subsequent operator review

The original worker record is retained above. [operator-review.md](operator-review.md)
records two numeric validation failures, their corrections, 37/297 passing tests
and unchanged trajectories/traces across all 357 regenerated cases.
