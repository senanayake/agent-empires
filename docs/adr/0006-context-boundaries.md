# ADR-006 — Context boundaries

- Status: proposed; tabletop recommendation, no architecture acceptance
- Date: 2026-10-08
- Scope: logical ownership inside the Python simulation
- Decision owner and review activity: AE-002 assigned Codex worker, author
  self-review; implementation review AE-007, evidence/learning revisit AE-013
- Related assumption IDs and superseded ADR: MA-01, MA-03, MA-06, MA-09;
  none superseded; preserves ADR-001

## Context and uncertainty

The campaign's logical context map is a hypothesis, not a requirement for nine
packages. Evidence in [T4](../../research/experiments/AE-002/tabletop.md#t4--conflicting-sources-with-shared-dependencies)
has an origin, a distribution history, an assessment and a decision use. Making
each consumer its owner would duplicate mutable facts and confuse access with
existence. Cross-owner atomicity is not yet tested.

## Alternatives and criteria

| Alternative | Ownership clarity and minimum implementation cost |
| --- | --- |
| One Decision aggregate owns the organization and evidence | Simple transaction surface, but T2 grant revocation and T4 source sharing span many decisions; bloated ownership and stale copies. |
| One package/service per campaign context | Visible boundaries, but no tabletop evidence justifies deployment, synchronization or package overhead. |
| Logical owners with ID/version references in one process | Preserves separate lifecycles with fewer structural commitments; needs explicit access views and coordinated commands. Preferred. |

## Decision and consequences

Propose [the context map](../context-map.md): keep Automation in Organization;
combine Work/Delivery and Software System responsibility for the single payment
service. Retain Intent/Goals, Knowledge/Communication, Decisions/Provenance,
Assurance and Outcomes/Learning responsibilities. Create modules only when a
later activity needs them.

L owns observations and belief/learning records; A owns assessments; K owns
items/holdings and delivery; D owns decision-use references. G enacts policy/goal
versions, while O recognizes scoped grants. World remains private within L;
Learning can use only available evidence. A known evidence ID is no access grant.
Application coordinates simulation operations; simulation cannot import
application or adapters. No new framework, transport or event store is selected.

## Evidence and validation

[AE-002 cross-case audit](../../research/experiments/AE-002/tabletop.md#cross-case-audit-and-disposition)
finds that T2 separates grant lifecycle from choice history, T3 separates belief
revision from policy enactment, and T4 needs several owners for distinct evidence
responsibilities. T4's assessment required its own delivery step; source delivery
alone was insufficient. These are worker-authored logical counterexamples, not
independent review, runtime tests or participant evidence.

## Revisit trigger

AE-007: a command leaves partial cross-owner state or dangling references.
AE-013: contested source lineage or a complete learning loop cannot be expressed
without duplicated mutable evidence/belief state. Merge or split the smallest
affected responsibility then; tabletop success alone does not accept the design.
