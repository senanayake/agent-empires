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

| ID / future filename | Initial status and recommendation | Alternative / trade-off | Decide or revisit |
| --- | --- | --- | --- |
| ADR-001 `0001-python-authority.md` | Constraint: Python is authoritative and independently reusable; domain has no UI/HTTP/Godot dependency. | Putting rules in Godot simplifies some UI code but defeats headless reuse and a single source of truth. | Record AE-001; dependency tests AE-007/020. |
| ADR-002 `0002-godot-presentation.md` | Constraint: Godot 4, 2D and GDScript for presentation/input. | Other renderers could be adapters later; early terminal experiments remain valid. | Record AE-021 after local tool verification; revisit only on a demonstrated boundary problem. |
| ADR-003 `0003-discrete-event-time.md` | Hypothesis strongly preferred: integer discrete-event time and stable priority/insertion ordering. | Fixed-step Python simulation may be simpler for a different mechanic; frame-driven domain behavior is excluded. | Decide AE-003; challenge same-time semantics and scheduling explosions AE-033. |
| ADR-004 `0004-seeded-randomness.md` | Constraint: seeded reproducibility; hypothesis: named/keyed RNG streams and pinned runtime are adequate. | One global stream is simpler but couples counterfactual draws; cross-runtime portable PRNG may be unnecessary. | AE-003/015; restore proof AE-031. |
| ADR-005 `0005-causal-history-and-replay.md` | Constraint: append-only causal event history; hypothesis: command replay first, full event sourcing deferred. | Reducer-based state reconstruction helps replay but adds schema/migration costs. A log alone does not guarantee restorable state. | Initial AE-003; evidence AE-010; finalize supported save/replay scope AE-031. |
| ADR-006 `0006-context-boundaries.md` | Hypothesis: logical DDD contexts in one Python process with narrow ID/version references. | Merge contexts where ownership remains simpler; do not create microservices. | AE-002; revise after evidence/learning AE-013. |
| ADR-007 `0007-actor-role-function.md` | Constraint: separate Actor, Role and OrganizationalFunction; hypothesis: explicit assignments plus holdings/graph edges suffice. | Inferring functions from a formal role hides the central replacement mechanic. Rich social simulation is deferred. | AE-002; implementation evidence AE-016–018. |
| ADR-008 `0008-decision-provenance.md` | Hypothesis: Decision is central, with independent resolution, authority and evidence axes and versioned provenance. | A lightweight versioned record may be enough; one “resolved” boolean is insufficient. | AE-002/006/007; revise with wrong-policy evidence AE-013. |
| ADR-009 `0009-transport-boundary.md` | Constraint: commands/snapshots/events cross an adapter; hypothesis: choose one local transport after a spike. | JSONL subprocess I/O versus localhost HTTP, with streaming only if polling is inadequate; lifecycle and test costs matter. | AE-020/022. No preselected FastAPI/WebSocket requirement. |
| ADR-010 `0010-scenario-format.md` | Hypothesis: versioned restricted YAML plus schema and content hash. | JSON reduces parser variation; Python scenarios permit accidental executable rules in data. | AE-008; choose based on readability, validation and portability. |
| ADR-011 `0011-no-external-llm.md` | Constraint: no external LLM dependency in MVP; deterministic rules/probabilistic Actor policies. | Optional future LLM adapter needs recorded inputs and separate reproducibility claims. | Record AE-020 (policy applies from the start); verify offline AE-032. |

Pydantic, HTTP framework choice, storage engine, packaging tool, human-response
rules, and the Assumption Debt formula remain unselected. Add an ADR only when a
consequential decision needs rationale; ordinary implementation choices need not
create an architecture document.
