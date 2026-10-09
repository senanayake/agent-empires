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

## AE-013 finite learning loops

`Learning` appends records referring to existing immutable objects. An
implementation fix replaces a proposal while retaining the work item and every
decision version, and requires recorded failing then passing chosen-spec checks.
Requirement revision appends a Decision version from accessible current usable
evidence supporting a different finite option. Verification, shared interpretation
roots, weak/stale/inaccessible claims and contradictions cannot justify that
revision; copying reports adds no roots or votes. Report meaning and source roots
remain trusted declarations, so even admitted independent reports can be wrong.

Policy interpretations reuse policy-scoped Decision versions rather than adding
a second mutable policy catalog. `assess_production` consumes only recorded
`OutcomeObserved` events, with matching outcome/deployment/decision lineage and
the recorded Goal. Deployment/operation is the sample identity. Duplicate
citations count once. Every admitted operation must have an available observation
whose physical outcome falls within the goal window; incomplete cohorts stay
pending. Observation arrival time may be later than the physical window.

The explicit MA-09 toy rule uses a declared minimum sample count and absolute
rate margin: fewer samples or an incomplete cohort is pending; abandonment at
or below the target passes; a miss at least the margin fails; a smaller miss
remains unknown. Rate comparisons use exact decimal rational thresholds. AE-013
uses four samples and margin 0.2; neither is a statistical significance claim.
A failure challenges the deployed interpretation, without identifying which
decision caused it or proving a remedy. Policy revision requires the current
pinned policy version, an old policy authorization and current scoped authority
for the alternative. Requirement learning cannot bypass this policy path.

The newly authorized choice remains an unvalidated hypothesis. A future deployment
pins it and receives its own fitness assessment; old feedback cannot update a
newer policy version. Goal, old proposals, old choices and deployment meaning stay
unchanged. Learning records and assessments are separate from authorization and
world outcomes. No automatic ship, goal discovery, empirical source authentication
or retrospective rewriting is added. See [AE-013 decision and scoped ledger](../research/experiments/AE-013/decision.md)
and [reproducible traces](../research/experiments/AE-013/loop-traces.json).

## AE-015 combined model gate and debt disposition

The [paired protocol](../research/experiments/AE-015/protocol.md) binds thirty root
seeds, both authored worlds, infer/clarify/feedback strategies and shared immutable
workload samples. The harness calls existing application/simulation APIs; it adds
no domain rules. Policy recommendations compare recorded observations from two
explicit intervention probes. An authored independent interface report supports
requirement revision; a goal miss alone supplies no causal remedy. Primary arms
retain five authority gaps despite six closed choices. The successful entire-roster
agent boundary uses recognized grants and explicit delegation, with zero gaps.

[Results and disposition](../research/experiments/AE-015/decision.md) retain failed
fitness, ties and sensitivity reversals. Complete-cohort rules leave missing or
copied feedback pending, and perfect observation remains an untested simplification.
Future exposure uses the same samples for a paired comparison, not independent
replication or held-out learning. No architecture acceptance or player evidence.

Accept removal of the **Assumption Debt scalar from planned gameplay** following
AE-014. Keep explicit uncertainty/impact/propagation/persistence/reversibility facts
beside concrete behavior, exposure and causal history. Historical diagnostic APIs
remain for research reproduction; do not use them for damage, correctness or a UI
risk score. This scope decision changes no runtime outcome rule or architecture.

## AE-016 live replacement composition

`Organization` separates formal roles and function assignments over the existing
KnowledgeStore roster. `members`, `role_for` and `function_holders` use live
presence; `uncovered_functions` exposes trusted diagnostics, not a player inventory.
The three Sarah functions in the scenario are independent of her title and of the
`historical_scope` holding. Assignment is coverage, not guaranteed performance.

`DeliveryService.register_actor(Actor, profile_id, role, command_id)` stages an
empty-access identity. `replace_actor(old_id, Actor, profile_id, role, command_id)`
accepts a new identity or an explicitly prepared present actor with the same
profile. Preflight validates identities, profile, role, command reuse and current
time before changes. It composes Organization/KnowledgeStore replacement, public
`AuthorityRegistry.revoke_actor`, `Communication.retire_actor`, and actual pending
job cancellation. Call existing send/assignment/delegation/connect APIs explicitly
for preparation; there is no automatic transfer, title-derived authority or trust.

KnowledgeStore exposes immutable roster entries, presence and actor registration;
IDs cannot be reused and new actors gain no artifact readers. Old holdings and
knowledge catalog stay in audit, unavailable through departed access. Owned grants
are revoked; descendant use fails ancestry checks. Historical choices retain their
old justification. A surviving issuer's independent delegation remains legitimate
for an agent but conveys no world evidence. Reconnection needs a new channel ID
and explicit endpoint/trust parameters; retired edges remain in historical audit.

The service's `communication` property initializes the authored graph on first
explicit use or validated replacement, on the same clock/store/history and with
currently present endpoints. Ordinary delivery adds no unused connection facts
or costs. `root_seed` selects existing named RNG streams (compatibility default 0);
experiments explicitly pin it. Channel retirement blocks new sends and preserves
admitted snapshots and costs: sender departure cannot recall them, recipient
absence emits `InformationLost`, and replacements never inherit queued recipients.

Unfinished jobs cancel immediately during service replacement, retaining costs and
causal links to WorkStarted/departure. Queue entries remain tombstones until their
scheduled ticks. `step` drains service messages and tombstones until the next live
proposal or exhaustion; no cancelled proposal appears. A direct KnowledgeStore
access-only departure also cancels unfinished jobs when dispatched, without full
organizational lifecycle composition. Already completed proposals and selected
decision versions remain immutable; new actors infer missing choices from current
access and their explicitly registered profile. At equal time, the command executed
first determines whether a job is still unfinished. Other owners' queued work still
requires their own dispatcher; no transport, second store/clock or transfer gameplay.

[AE-016 review](../research/experiments/AE-016/review.md) records model limits,
paired loss seeds and preserved regression failures. No traffic is shipped by
these replacement traces; uncovered coverage alone proves no payment incident.
