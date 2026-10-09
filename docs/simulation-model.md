# PaymentCo input and simulation boundary

AE-008 authors [scenario.json](../scenarios/paymentco/scenario.json) under
[ADR-010](adr/0010-scenario-format.md). Existing simulation owners remain the
authority for time, randomness, history, holdings, communication and decisions.
This activity supplies initial data and validation; payment outcomes, work
execution, learning and replacement functions remain later campaign activities.

`application.scenarios.load_scenario(path, expected_hash=...)` reads strict UTF-8
JSON, validates the bundled schema and typed references, and returns a trusted
`Scenario` owner. `sha256` identifies exact file bytes. Compatible data uses schema
1, scenario major 1 and model `paymentco-inputs-v1`. The file's seed contract
requires an explicit integer root seed and named streams when running the engine;
loading never samples randomness or chooses a world. Persist engine/RNG versions,
CPython 3.12.13, world ID, scenario version/hash and ordered commands in each run.

Goal is a measure/window/target, current policies are scoped authorized beliefs,
and the two private worlds supply exogenous toy parameters. The categories are
transient, soft decline, hard decline and ambiguous; mix probabilities are
conditional on an eligible failed payment and sum to one. Recovery parameters
are proposed category chances, not observed evidence or a complete outcome
formula. AE-010 must specify exposure, idempotency, retry/backoff effects and
sampling. No category or actor carries an `is_correct` flag. Zero workload is
valid; any future transaction incident must require actual modeled exposure.

Every operational numeric input is a parameter record. Probability is bounded
by [0, 1]; time uses integer ticks, channel admissions use messages/tick, costs
use integer toy resource units, retry counts use attempts, and arrivals use
payments/tick. Schema versions and item/policy revisions are structural metadata,
not tunable probabilities. Admissible and sensitivity ranges are explicit and
checked. All current sources are `invented for experiment` with null calibration
version. Values and mechanisms remain uncertain even when validation passes.
Goal, world, channel and profile references require their expected units.

Actors share one schema; three optional agent capability bundles and one human
bundle use AE-006's `CapabilityProfile`. Preference orders must rank exactly the
decision alternatives. Work speed/cost/availability are declared future inputs;
the loader does not implement those behaviors. Formal role labels, informal
function assignments, scoped root grants and holdings remain independent.
Root authority is trusted organizational setup, not evidence or a grant from
actor kind. Policy actor, scope and selected option must match a grant.

Knowledge items are retained even with no accessible holder. Holdings pin item
versions, personal/artifact holder, declared source roots, confidence, freshness,
explicitness and access. Artifacts require explicit reader IDs; a source ID is
provenance and supplies no lookup capability. `instantiate_knowledge(history)`
creates a fresh AE-004 store and records explicit tick-0 holding events in the
caller's history. These are trusted setup facts, not inferred transfers. Channel
inputs do not create holdings. Profile, function or grant assignment copies none.

`knowledge_for` and `snapshot_for` are detached **initial-state** projections.
They expose the public goal values, thin work item, formal roster, alternatives
and the viewer's accessible holdings. They omit world answers, private parameter
catalog, policy/source catalogs, function assignments and other actors' claims.
`audit_data` is for trusted setup/review only. Do not pass the `Scenario` owner to
actor policies or presentation. After runtime changes, services must query their
live store; an initial snapshot is not current permission. Python introspection
and malicious authors are outside this API boundary's security claim.

The initial graph, decision options, roster and variant values are in the
[scenario brief](../scenarios/paymentco/README.md). Numeric option semantics
declare caps/delays; adaptive retry/update rules remain unresolved for AE-009/013.
Snapshots and loader checks do not establish empirical calibration, usability,
real payment correctness, safety, architecture acceptance or campaign completion.
