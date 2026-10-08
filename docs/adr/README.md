# Architecture decision record register

The user brief supplies product/technology constraints. This register proposes
decisions and their review points; it does not claim that implementation evidence
already exists. Use [the template](template.md). Record context, alternatives,
consequences, evidence, status and a concrete revisit trigger. Supersede rather
than rewriting the rationale of an accepted historical decision.

Statuses: **constraint** (specified by the brief), **hypothesis** (must be tested),
then **proposed**, **accepted**, **superseded**, or **rejected** in individual ADRs.
A constraint can still be revisited by an explicit product decision. Hypotheses
must not be promoted to permanent architecture simply because a file exists.

| ID / filename (unlinked files are future work) | Status and recommendation | Alternative / trade-off | Decide or revisit |
| --- | --- | --- | --- |
| [ADR-001](0001-python-authority.md) | Accepted as an existing product constraint in AE-001: Python is authoritative and independently reusable; domain has no application/adapter/UI/HTTP/Godot/controller dependency. Implementation and architecture acceptance remain unverified. | Putting rules in Godot simplifies some UI code but defeats headless reuse and a single source of truth. | Worker self-review in AE-001; dependency tests AE-007/020 and frame-rate test AE-022 remain future work. |
| ADR-002 `0002-godot-presentation.md` | Constraint: Godot 4, 2D and GDScript for presentation/input. | Other renderers could be adapters later; early terminal experiments remain valid. | Record AE-021 after local tool verification; revisit only on a demonstrated boundary problem. |
| ADR-003 `0003-discrete-event-time.md` | Hypothesis strongly preferred: integer discrete-event time and stable priority/insertion ordering. | Fixed-step Python simulation may be simpler for a different mechanic; frame-driven domain behavior is excluded. | Decide AE-003; challenge same-time semantics and scheduling explosions AE-033. |
| ADR-004 `0004-seeded-randomness.md` | Constraint: seeded reproducibility; hypothesis: named/keyed RNG streams and pinned runtime are adequate. | One global stream is simpler but couples counterfactual draws; cross-runtime portable PRNG may be unnecessary. | AE-003/015; restore proof AE-031. |
| ADR-005 `0005-causal-history-and-replay.md` | Constraint: append-only causal event history; hypothesis: command replay first, full event sourcing deferred. | Reducer-based state reconstruction helps replay but adds schema/migration costs. A log alone does not guarantee restorable state. | Initial AE-003; evidence AE-010; finalize supported save/replay scope AE-031. |
| [ADR-006](0006-context-boundaries.md) | Proposed after AE-002 tabletop: logical owners with ID/version refs; combine Work/Software System and keep Automation in Organization. | Avoid duplicated evidence ownership and premature packages; no microservices. | Worker self-review AE-002; atomicity AE-007, evidence/learning AE-013. |
| [ADR-007](0007-actor-role-function.md) | Proposed representation of the Actor/Role/OrganizationalFunction separation constraint: distinct assignments, grants and holdings. | Role-derived functions/authority fail the tabletop; rich social simulation remains deferred. | Worker self-review AE-002; replacement/relabeling evidence AE-016–018, discovery AE-019. |
| [ADR-008](0008-decision-provenance.md) | Proposed after AE-002: small immutable choice/justification versions; independent selection, authority and evidence. | Combined status rejected; heavy aggregate ownership is not justified by the five cases. | Worker self-review AE-002; transitions AE-006, gate AE-007, wrong-policy learning AE-013. |
| ADR-009 `0009-transport-boundary.md` | Constraint: commands/snapshots/events cross an adapter; hypothesis: choose one local transport after a spike. | JSONL subprocess I/O versus localhost HTTP, with streaming only if polling is inadequate; lifecycle and test costs matter. | AE-020/022. No preselected FastAPI/WebSocket requirement. |
| ADR-010 `0010-scenario-format.md` | Hypothesis: versioned restricted YAML plus schema and content hash. | JSON reduces parser variation; Python scenarios permit accidental executable rules in data. | AE-008; choose based on readability, validation and portability. |
| ADR-011 `0011-no-external-llm.md` | Constraint: no external LLM dependency in MVP; deterministic rules/probabilistic Actor policies. | Optional future LLM adapter needs recorded inputs and separate reproducibility claims. | Record AE-020 (policy applies from the start); verify offline AE-032. |

AE-001 selects CPython 3.12.13 and uv with `uv.lock` for the execution baseline;
AE-003 creates the package/environment and chooses its packaging backend. See
[development](../development.md) and the [activity receipt](../campaigns/mvp/evidence/AE-001.json).
AE-002 records ADR-006/007/008 as proposals supported only by
[authored tabletop counterexamples](../../research/experiments/AE-002/tabletop.md).
No architecture acceptance or implementation proof is implied. The remaining
unlinked ADRs are future constraints or hypotheses, not accepted designs.

Pydantic, HTTP framework choice, storage engine, packaging backend, human-response
rules, and the Assumption Debt formula remain unselected. Add an ADR only when a
consequential decision needs rationale; ordinary implementation choices need not
create an architecture document.
