# ADR-007 — Actor, Role and OrganizationalFunction

- Status: proposed representation of an existing product constraint
- Date: 2026-10-08
- Scope: organization identities, assignments, authority and knowledge access
- Decision owner and review activity: AE-002 assigned Codex worker, author
  self-review; implementation/replacement review AE-016–018
- Related assumption IDs and superseded ADR: MA-03, MA-05, MA-06, MA-11;
  none superseded

## Context and uncertainty

The campaign requires Actor, Role and OrganizationalFunction to remain distinct.
Sarah's historian/translator work is not implied by a senior-engineer title;
an agent can perform the same function if it has the relevant capabilities and
access. A role change cannot silently copy knowledge or grant discretion.
Whether simple assignments/holdings suffice for discoverable gameplay is unknown.

## Alternatives and criteria

| Alternative | Causal clarity and scope |
| --- | --- |
| Derive function, knowledge and authority from role or actor kind | Small data model, but contradicts delegated agents (T2) and inaccessible rationale (T1/T3). Rejected. |
| Explicit role/function assignments, holdings, grants and graph edges | Preserves independent causes; preferred initial representation, needs actual transition tests later. |
| Rich social/enterprise ontology | Could express more informal behavior, but adds unsupported mechanisms outside MVP scope. Deferred. |

## Decision and consequences

Propose one Actor abstraction for humans and agents. O owns capabilities, role
assignments, function coverage, relationships and scoped grants; K owns holdings
and transfer paths. Work records reference responsible Actors. A function can be
shared or uncovered; coverage does not guarantee successful performance.

Assigning a role does not change grants, holdings, trust edges or informal
function coverage. A replacement command must separately account for those
records and interrupted work. Authority requires a recognized scoped grant, not
a role label. Access requires a usable holding, not the scenario's audit copy.
No rule branches on Sarah's name or a human/agent label to determine harm.

## Evidence and validation

[T2](../../research/experiments/AE-002/tabletop.md#t2--legitimate-delegation-without-world-evidence)
requires an explicit grant for agent a1 despite its developer assignment; changing
its kind to human supplies no evidence or permission. T1's Jin cannot use Ada's
contract until delivery; T3's accessible policy does not transfer Sarah's tacit
rationale. The cross-case role-transfer probe rejects implicit copying.
These manual counterexamples support the separation, not a working replacement
mechanic. No actual actor simulation or human study was performed.

## Revisit trigger

AE-016–018 must exercise sole-holder loss, redundant coverage, interrupted work,
complete transfer, matched-profile relabeling and successful all-agent continuity.
If explicit assignments cannot represent a demonstrated dependency, revise the
smallest missing relation. AE-019 must test whether players can discover functions
without an omniscient inventory; richer social rules remain deferred under MA-13.
