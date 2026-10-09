# AE-009 bounded experiment

Question: can an executable proposal conform to its chosen interpretation while
its authority, independent support and appropriateness remain unproven?
Authored before generating green-change.json. No random draws: seed set is empty,
root seed null; seeded world/workload outcomes belong to AE-010. Repeated canonical
histories and actor-kind/world controls replace irrelevant seed repetition here.

Controls: Jin with human profile; Jin with implementer profile; the same
implementer profile relabeled human; an implementer with omitted retries; an
implementer with changed private World A recovery; adaptive and selected-category
preferences without required refinements. Each starts one work command then steps
one completion. Modified scenarios are temporary trusted setup inputs; original
PaymentCo bytes remain unchanged. Variant exact-byte hashes are recorded.

Predictions/falsifiers: implementer duration/cost 1 tick/2 resource units versus
human profile 5/5 (MA-05, invented); both can be green, including zero retries.
Changing only actor kind or private recovery must preserve canonical history and
proposal results. A three-retry choice implemented with zero retries must fail
conformance. No check can establish requirement fitness, architecture or security.
Refinement refusal must retain state/cost, rather than invent adaptive/category
semantics. Every negative result stays in the artifact; no success filtering.

Metrics: completion tick, admitted resource cost, pinned decision versions,
unsupported refs, check results, dimension statuses, canonical history and hashes.
Use `python3 research/experiments/AE-009/delivery_experiment.py --verify-against
research/experiments/AE-009/green-change.json` to reproduce without overwriting.
Speed/cost are per work item (paid once at start); durations ignore availability
and capacity. Work admitted before departure completes, with cost retained.

Retry-plan-v1 is an invented engineering mechanism: plan all additional attempts
if failure continues, filter base categories by decline choice, cumulative fixed
or capped doubling delay, explicit operation keys and audit mode. Zero cap/delay
and unspecified key are legal. Adaptive retry and selected-category refinement
are deliberately unavailable; this does not prevent the bounded three/none slice.
No payment execution, deployment, success probability, audit scanner or learning
is implemented. All unassessed dimensions remain unknown. Evidence sources are
pinned choices; conformance supplies no independent evidence about those choices.
