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
| [ADR-003](0003-discrete-event-time.md) | Proposed and implemented in AE-003: integer ticks, priority/insertion order; worker tests pass, no architecture gate. | Fixed steps remain an option for another mechanic; pending work is dispatched by the caller. | Composition AE-007; rendering AE-022; scheduling budgets AE-033. |
| [ADR-004](0004-seeded-randomness.md) | Seeded reproducibility constraint; named SHA-256/MT19937 scheme implemented and tested under CPython 3.12.13. | Unrelated streams isolate draws; extra draws within one stream still shift counterfactual samples. | Paired workload alignment AE-015; restoration AE-031; any runtime/scheme change. |
| [ADR-005](0005-causal-history-and-replay.md) | Append-only history constraint; immutable facts and command-fixture replay implemented and worker-tested. | No reducers or full event sourcing; canonical history is not proof of restorable domain state. | Composition AE-007/010; supported save/replay scope AE-031. |
| [ADR-006](0006-context-boundaries.md) | Proposed; AE-013 implements separate assessment/revision records and reuses policy-scoped Decision versions. | Avoid duplicated evidence ownership and premature packages; no microservices or architecture acceptance. | AE-013 worker evidence; sensitivity AE-015, restoration AE-031. |
| [ADR-007](0007-actor-role-function.md) | Proposed representation of the Actor/Role/OrganizationalFunction separation constraint: distinct assignments, grants and holdings. | Role-derived functions/authority fail the tabletop; rich social simulation remains deferred. | Worker self-review AE-002; replacement/relabeling evidence AE-016–018, discovery AE-019. |
| [ADR-008](0008-decision-provenance.md) | Proposed; AE-013 revisions retain old proposal, requirement, policy and deployment meaning. | A goal miss challenges an interpretation; the authorized replacement stays unvalidated until future observed exposure. | AE-013 worker evidence; threshold/source sensitivity AE-015; no architecture acceptance implied. |
| ADR-009 `0009-transport-boundary.md` | Constraint: commands/snapshots/events cross an adapter; hypothesis: choose one local transport after a spike. | JSONL subprocess I/O versus localhost HTTP, with streaming only if polling is inadequate; lifecycle and test costs matter. | AE-020/022. No preselected FastAPI/WebSocket requirement. |
| [ADR-010](0010-scenario-format.md) | Proposed and implemented in AE-008: strict UTF-8 JSON, schema/reference/provenance checks and exact-byte SHA-256; worker tested, no architecture acceptance. | JSON replaces planned YAML to avoid parser variation; a bounded standard-library schema evaluator has no new dependency. | Schema vocabulary expansion, packaging AE-032, world rules AE-010 and snapshot boundary AE-020/026. |
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
