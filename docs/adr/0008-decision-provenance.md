# ADR-008 — Decision provenance

- Status: proposed; lightweight versioned model favored by tabletop only
- Date: 2026-10-08
- Scope: decision consistency boundary, authority and evidence references
- Decision owner and review activity: AE-002 assigned Codex worker, author
  self-review; transitions AE-006, gate AE-007, learning revisit AE-013
- Related assumption IDs and superseded ADR: MA-01, MA-02, MA-06, MA-09;
  none superseded

## Context and uncertainty

Decision is central to the explanation but need not own every source of that
explanation. Selection can occur without a grant, delegation without world
evidence, and authorization with poor outcomes. A single resolved/correct status
cannot preserve these cases. The smallest enforceable runtime boundary is still
unknown; AE-002 creates no code or evidence of replay/atomicity.

## Alternatives and criteria

| Alternative | Expressiveness and consistency cost |
| --- | --- |
| One resolution boolean or inferred/delegated/evidenced enum | Cannot represent T2's delegated, unsupported choice or T3's authorized, challenged policy. Rejected. |
| Heavy aggregate owning grants, evidence, beliefs and implementation | Broad transaction control, but shared sources/grants would have competing lifecycles and ownership (T2/T4). Not justified. |
| Stable identity plus immutable choice/justification versions and external refs | Expresses all five sketches with local membership/version checks; preferred pending transition tests. |

## Decision and consequences

Propose the [small Decision model](../domain-model.md#decision-identity-and-versions).
Selection, authority basis/evaluation, evidence relationships, confidence and
assurance dimensions stay separate. Authority is evaluated for a scoped action
at a time, with historical refs preserved after revocation. An authority record
can evidence permission without supporting a claim about world fitness.

Append choice or justification revisions; retain alternatives and old versions.
Evidence can change while the chosen value stays the same (T5). Proposals and
deployments pin versions. Source lineage includes shared dependencies and known
missing information at selection time. Do not infer independence from a second
actor/report or infer information gain from closure.

Assumption is a recorded justification gap, not a direct input to damage. Outcomes
consume deployed behavior and exposure. No global correctness flag, numerical
entropy, universal confidence calculus or full event-sourcing commitment is added.
Cross-owner orchestration and invalid/stale reference handling need later tests.

## Evidence and validation

[The tabletop](../../research/experiments/AE-002/tabletop.md) records five full
forward/backward walks: T1 inferred/green, T2 delegated without world evidence,
T3 wrong authorized policy, T4 conflicting/dependent sources, T5 harmless
unsupported choice. The combined status fails these manual counterexamples;
the smaller proposed model preserves them. T3's trial required explicit exception
authority; T5 success still could not legitimate the decision. No independent
domain review, implemented transition tests or empirical validation is claimed.

## Revisit trigger

AE-006/007: immutable local versions cannot enforce an actual invariant, stale
command or revoked-grant case; add only the necessary consistency boundary.
AE-013: evidence cannot revise belief, decision and policy separately while
preserving prior deployment meaning. Revisit finite alternatives under MA-01 if
a concrete PaymentCo counterexample cannot be represented without false certainty.
