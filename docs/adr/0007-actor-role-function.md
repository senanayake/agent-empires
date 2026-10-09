# ADR-007 — Actor, Role and OrganizationalFunction

- Status: accepted bounded implementation choice; worker engineering self-review,
  no independent architecture or domain acceptance
- Date: 2026-10-09 (AE-002 proposal remains the original rationale)
- Scope: organization identities, assignments, authority and knowledge access
- Decision owner and review activity: AE-016 assigned Codex worker, self-review;
  deliberate transfer/composition/discovery review remains AE-017–019
- Related assumption IDs and superseded ADR: MA-03, MA-05, MA-06, MA-11;
  none superseded

## Context and uncertainty

The product requires Actor, Role and OrganizationalFunction to remain distinct.
Sarah's historian/translator work is not implied by a senior-engineer title.
AE-002 proposed explicit assignments from tabletop counterexamples; AE-016 now
exercises them in live delivery. Whether this produces discoverable, interesting
player choices remains unproven. No real organizational calibration is claimed.

## Alternatives and criteria

| Alternative | Causal clarity and scope |
| --- | --- |
| Derive function, knowledge and authority from role or actor kind | Small, but contradicts delegated agents and inaccessible rationale. Rejected. |
| Explicit assignments, holdings, grants and edges | Selected: preserves independent causes with public lifecycle operations and actual interrupted work. |
| Rich social/enterprise ontology | Adds unsupported mechanisms outside MVP. Deferred. |

## Decision and consequences

Use one Actor abstraction for humans and agents. Organization owns role/function
assignments over KnowledgeStore's live roster and team memberships. KnowledgeStore
owns holdings/access, AuthorityRegistry owns scoped grants, and Communication owns
directed edges and admitted snapshots. DeliveryService coordinates these public
owners, explicit current profiles and actual queued work. Function coverage means
assignment, not proof of capability, knowledge, trust or successful performance.

Replacement accepts a new empty-access identity or an explicitly prepared present
actor. It removes the departing actor's roles, memberships/access and function
assignments, revokes owned grants (invalidating descendants), and retires incident
channels. IDs cannot be reused. New roles/teams/profiles are explicit inputs and
copy no holdings, grants, trust or functions. Prepared actors keep only their own
state/profile. Independent surviving issuers can delegate to agents; authority
adds neither knowledge nor evidence. New connections specify their own trust.

Unfinished delivery work is cancelled with history and charged resources retained;
queued completions become tombstones. Completed proposals remain immutable. A
KnowledgeStore-only departure also prevents work completion at dispatch, while
that access-only API does not compose the other lifecycle owners. Admitted sender
snapshots survive retirement; a departed recipient loses the message. No implicit
retargeting, refund, automatic incident, actor-name penalty or transfer gameplay.

## Evidence and validation

[T2](../../research/experiments/AE-002/tabletop.md#t2--legitimate-delegation-without-world-evidence)
provided the original authority-without-knowledge counterexample. AE-016 adds
[live replacement tests](../../tests/simulation/test_replacement.py),
[seven traces and sixteen paired seeds](../../research/experiments/AE-016/replacement-traces.json)
and [worker review](../../research/experiments/AE-016/review.md). They cover departure
cancellation, new-actor work, redundancy, delegation, removed bridges, equal-time
ordering, rejected-command nonmutation, matched kind/profile and renamed actors.
Original red failures and negative seeds remain in experiment artifacts.

Explicit preparation preserves modeled coverage/access and matched work behavior,
at recorded time and channel cost. Assignment alone supplies no tacit rationale.
The existing regression that expects departed work to finish conflicts with the
operator's cancellation correction and lies outside AE-016's allowed test paths.
Historical AE-013 replay also detects the changed scenario hash; every other
JSON-normalized trace field matches. Historical evidence is preserved unchanged.
No player, independent domain, integration or publication claim follows.

## Revisit trigger

AE-017–018 must examine deliberate transfer trade-offs and organization-wide
agent continuity. Revise the smallest missing relation if a demonstrated dependency
cannot be represented. AE-019 reviews discoverability without an omniscient
inventory; actual comprehension belongs to AE-029. Social rules remain deferred.
