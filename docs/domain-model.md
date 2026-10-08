# Candidate domain model: versioned choices with explicit owners

AE-002, 2026-10-08; **proposed**, not implemented or architecture-accepted.
The [tabletop](../research/experiments/AE-002/tabletop.md) favors a small Decision
record over a transaction owning the organization. [ADR-008](adr/0008-decision-provenance.md)
records this bounded recommendation. Python authority from ADR-001 remains fixed.

## Decision identity and versions

A stable `decision_id` identifies one scoped question (for example, this Work
Item's `retry_count`). Each immutable version contains:

- Question/scope and named alternatives; selection is null or one alternative.
- Prior version, author Actor ID, recording event and goal/policy version refs.
- Claimed authority basis and the evaluated grant/policy refs **at this version's
  recording time**, including unresolved/conflicting findings and the original
  selection event ref. Current permission is evaluated again for a later action;
  revocation does not rewrite the authority recorded for the original selection.
- Reasoning/provenance, known missing-information dependencies, evidence refs with
  target propositions and source dependencies, and referenced belief versions.
- Qualitative confidence/support with reasons, plus impact/reversibility notes
  where known. Unknown stays explicit; no numeric debt/entropy formula is selected.

Append a version to change choice, alternatives, scope or justification; an
evidence-only revision can preserve selection. A historical version remains
addressable even after another becomes current. A proposal/deployment pins exact
versions, so late observations can still concern an old implementation.

This is a small consistency boundary: validate membership, version succession,
references and provenance at command time. It need not be an event-sourcing
framework or a large mutable aggregate. Foreign evidence and grants retain their
owners; Decision stores refs and the historical evaluation, not competing copies.
AE-006 will select concrete types/transition APIs and AE-007 will test them.

## Ownership and command boundaries

| Owner (logical simulation responsibility) | Authoritative state | References/coordination |
| --- | --- | --- |
| Intent and Goals (G) | Intent, goal measures/windows, enacted policy text/scope/versions | Policy authorization references Organization; factual rationale references Learning beliefs. Learning proposes revisions; G appends enacted versions. |
| Organization (O) | Actors, capabilities, memberships, role assignments, function coverage, recognized grants/revocations | Holdings live in K; roles/functions/grants have distinct records. Actor can expose refs without owning their lifecycle. Automation is an O policy. |
| Knowledge and Communication (K) | Items/versions, holdings/access/freshness, channels and transfers | Evidence content can be carried as an item referring to its originating record; distribution never changes that record. |
| Decisions and Provenance (D) | Decision identity and immutable versions | Reads available K refs, O grants, G scope, A assessments and L belief/observation refs. It cannot grant authority or declare world truth. |
| Work and Delivery (W) | Work Items, proposals, deployed software behavior | Pins D versions; shipping permission and assessment policy are separate preconditions. Start with one service; Software System is a responsibility here. |
| Assurance (A) | Versioned assessments, method, subject/version, dimension, result and evidence lineage | Verification and validation both name their criterion; A cannot mutate decisions or observed outcomes. |
| Outcomes and Learning (L) | World rules/consequences, separately published observations; belief versions and learning records | World is private. Learning consumes available observations, never private rules. It requests D/G revisions rather than overwriting their state. |

The application coordinates a command across these owners using simulation
operations. Simulation never imports application. Time/history remain Python
simulation concerns (AE-003). Logical ownership is not a package/service mandate.
Cross-owner atomicity and rollback are unresolved until AE-007; one command must
not publish success for a partial transfer or a dangling revision.

## Invariants challenged in AE-002

| ID | Rule | Counterexample / review |
| --- | --- | --- |
| I1 | A selected value belongs to that version's alternatives; versions append, and deployed refs remain pinned. | T2 rejects count four, outside the alternatives; T3 leaves the old no-retry deployment intact after revision. |
| I2 | Selection, legitimate authority and evidential support vary independently. | T1 selected without a grant; T2 delegated without outcome evidence; T3 authorized but challenged; T5 unsupported without harm. |
| I3 | Validate grantor, recipient, action, option/scope, validity and delegation chain. No grant by actor kind or role name. | T2 invalid count, revocation and relabeling probes; T1 Ada's inaccessible contract is not Jin's permission. |
| I4 | Access is explicit and time-bound; audit storage and source refs do not create holdings. | T1 recorded missing interface rationale; T3 Sarah's tacit rationale; T4 an undelivered source cannot change belief. |
| I5 | Assessments name subject/version, dimension/method and source dependencies; copying does not add independent support. | T1 green tests of the inferred spec; T4 two copies of one report against a separately collected observation. |
| I6 | Outcomes depend on behavior and world exposure, not actor kind, authority or an unsupported-choice flag. | T1 duplicate exposure; T5 no difference in exposed behavior; no-traffic control has no transaction incident. |
| I7 | Observations retain workload/event/detection/availability times and deployed refs; learning is a separate recorded act. | T3 evidence from an old policy remains about that policy after a new choice. |
| I8 | Role assignment, function coverage, grants and holdings change separately. | T2 an agent's developer role supplies no grant; moving Sarah's historian function alone cannot copy her rationale. |
| I9 | Facts have stable IDs, integer ticks, total order, schema/version refs and earlier typed parents; no retrospective causal fabrication. | Every T1–T5 trace distinguishes direct causes, support and association, retaining missing refs recorded at choice time. Replay remains unimplemented. |

## Candidate events and epistemic limits

Use the campaign's event envelope. The tabletop adds descriptive candidate facts
`DecisionSelected`, `DecisionRevised`, `AuthorityRevoked`, `PolicyRevised`,
`AssessmentRecorded` and `WorldOutcomeOccurred`; names/schema are not committed
APIs. `DecisionDelegated` records O's grant, not a change to evidence.
`AssumptionMade` may annotate the same command as `DecisionSelected`; it records
a gap rather than being another choice or a damage trigger. A failed command
does not emit a successful domain fact.

`WorldOutcomeOccurred` can be private audit history. `OutcomeObserved` records
the later sample and its availability; those are distinct from an incident label.
`BeliefRevised` belongs to L; `DecisionRevised` to D; `PolicyRevised`/`GoalRevised`
to G. Revisions cite the relevant evidence but cannot invent it. Supporting
evidence edges are not direct causes of a payment failure. An association edge
alone is insufficient for a causal explanation.

## Unresolved boundaries and next falsifiers

- **Evidence spanning owners:** L owns observations, A owns assessments, K owns
  access, D owns usage/justification. AE-013 must test whether a small shared
  evidence-reference value type suffices for mixed methods and contested lineage;
  a new evidence aggregate is not yet justified (T4).
- **Belief and policy:** L records epistemic revision; G enacts normative change.
  AE-013 must demonstrate separate implementation, interpretation and goal/policy
  loops. A factual update cannot silently revoke a policy (T3).
- **Authority conflicts:** preserve conflicting grants/policies and require a
  scoped resolution; no universal hierarchy or majority-vote rule is proposed.
  AE-006 must define expiry and invalid-reference errors without banning the
  deliberately modeled unsupported choices (T1/T2).
- **Concurrency and atomicity:** ordered commands may suffice, but stale expected
  versions and cross-owner partial failure need AE-006/007 tests. Add a heavier
  aggregate only if those tests expose an invariant the small record cannot enforce.
- **Function discovery:** coverage records are model state; observable interactions
  must justify what a player learns. AE-016–019 must challenge sole-holder and
  redundant-holder cases; tabletop relabeling is not implementation proof.
