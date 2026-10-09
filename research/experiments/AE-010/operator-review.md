# AE-010 operator review

Disposition: accept the bounded causal payment slice after numeric corrections.
The root operator separately read the outcome owner, all tests, paired experiment,
protocol, current/preserved traces, per-seed analysis, worker review and assumptions
changes. This is machine review, not a participant or empirical calibration.

Two actual failing probes are retained in `operator-numeric-red.json`: an oversized
integer probability raised incidental OverflowError, and a valid scenario mixture
accepted at the loader's rounding tolerance was rejected by WorldRules. Probability
bounds now reject oversized inputs before float conversion; normalization uses the
loader's 1e-9 tolerance. `operator-numeric-green.json` records 37 focused / 297 total
passing tests. The exact correction is in `operator-review-diff.json`. Original
worker source, compressed runs/traces, timing and receipt remain archived in
`before-numeric-review/`; original 35/295 statements are historical.

All 357 cases were regenerated. `operator-comparison.json` verifies identical
trajectories, controls, per-seed analysis and canonical trace bytes; only the source
hash changed in the manifest. No current physical rule or toy world value changed.
Model version remains payment-outcomes-v1 for this compatible validation correction;
exact source hashes remain part of the reproduction contract. Fresh timing remains
inside the declared budget.

Seeded draws are fixed per operation/ordinal, independent of strategies and actor
labels. Harm requires actual exposure and successful duplicate execution. No-traffic,
zero-exposure, harmless-assumption, policy reversal and human/agent controls prevent
forced moral outcomes. Decisions/proposals/deployments remain pinned; incident links
identify the actual attempt and relevant predeployment idempotency gap. Gap edges
are associations, never damage causes. Monitoring comparisons exclude only opaque
interleaved event IDs and retain every physical field and metric.

Limits for successors: results, metrics and raw history are privileged world audit;
player projections must use delayed observations and redact undisclosed inputs.
Known risks may have no recorded gap; do not manufacture one to satisfy a narrative.
Physical hidden commit counts as completed and excludes abandonment even without
acknowledgment: this is a customer-response simplification to challenge in AE-015.
Perfect monitoring, independent ordinal draws, finite failed-payment traffic and
single readiness threshold are toy assumptions. Queue ownership currently changes
only after delivery is quiescent; general mixed-owner dispatch remains future work.
Authority/evidence/learning, human comprehension and the full game are unproven.
Controller validation/local delivery are still separate; no publication is claimed.
