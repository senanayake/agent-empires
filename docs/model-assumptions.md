# Model assumptions and research integrity

Planning baseline: 2026-10-08. No empirical calibration has been performed.
The simulator begins as a conceptual model. A reproducible toy result supports a
claim about that model, not a causal claim about real organizations or payments.

The campaign's activity IDs identify who revisits each assumption. “Owner” means
the executing activity's maintainer, not an assignment to an outside person.
Keep replaced hypotheses and failed experiments in history.

| ID | Assumption / classification | Proposed representation and uncertainty | Evidence that challenges it / owner |
| --- | --- | --- | --- |
| MA-01 | Finite decision alternatives are useful — structural hypothesis | Six PaymentCo questions with explicit alternatives; selected values, organizational beliefs and world behavior remain separate. Real semantic uncertainty is richer. | Tabletop contradictory examples; expand only if the finite model cannot explain them. AE-002/006. |
| MA-02 | Confidence and uncertainty can be tracked without a truth oracle — structural hypothesis | Begin with categories and provenance; if numerical beliefs are needed, define a normalized distribution over named hypotheses and an explicit update rule. Agent confidence bias is separate. Entropy is about that distribution, not correctness. | Unsupported certainty, conflicting evidence and wrong authorized policy; reject any update that counts choosing as learning. AE-006/013. |
| MA-03 | Holdings approximate organizational knowledge access — structural hypothesis | Item/version plus holder/access/freshness; tacit-only holdings may disappear on departure. Audit records are not automatically actor-accessible. Freshness initially uses age or explicit invalidation, not a universal decay curve. | Redundant holders, inaccessible documents, sole-holder loss and later rediscovery. AE-004/017. |
| MA-04 | Channels can be reduced to capacity, latency, loss and distortion — toy mechanism | Integer ticks, messages per tick, delivery probability, distortion probability, trust and cost; distortion must produce a defined alternative proposition and retain origin. Independence of transfer failures is initially assumed and must be tested against correlated-loss variants. | Zero/full loss, congestion, shared sources, topology trade-offs and sensitivity ranges. AE-005/018. |
| MA-05 | Capability profiles create useful automation temptation — toy gameplay parameters | Shared Actor policies for speed, cost, inference accuracy, clarification threshold, review and availability. Human/agent label alone changes nothing. Values are selected only in scenario data with units and rationale. | Matched-profile relabeling, human failure, agent success and player choice; don't force a throughput advantage to outweigh every other dimension. AE-009/018/029. |
| MA-06 | Scoped authority/provenance are distinct from evidence — domain hypothesis | Explicit grant/delegation/policy constraint or unsupported inference; authority can change without new world evidence. Source chains retain shared dependencies. Agents may receive authority. | Delegated but wrong decision, unsupported but successful choice, copied verification, revoked authority. AE-002/006/013. |
| MA-07 | A small fictional payment world is sufficient — toy environment | Workload classes, recovery chances, duplicate effects, retry costs and abandonment response; Goal measures abandonment separately from operational harm/cost. Initial decline policy is a hypothesis, not legal or financial guidance. | At least two worlds with different trade-offs, no-traffic control, benign/harmful assumptions and policy reversal after evidence. AE-008/010/015. |
| MA-08 | Observation lag can explain delayed consequences — toy parameter | Separate workload time, event time, detection time and availability of feedback. Observation delay is configurable; no timer punishes actor replacement. | Fast/slow monitoring, incident-free runs and delayed evidence from old versions. AE-010/027. |
| MA-09 | Explicit finite rules can model belief revision — structural hypothesis | Evidence has subject, source, method, version, quality and independence links. Update rules may retain uncertainty. Verification generated from the same interpretation cannot independently validate that interpretation. | Noisy evidence, wrong policy, feedback ablation and three distinct loop traces. AE-013/015. |
| MA-10 | Assumption Debt may summarize exposure — optional diagnostic hypothesis | Candidate Impact × Uncertainty × Propagation × Persistence. Define normalized scales and observation windows before use; record reversibility separately or as an explicit modifier. Never directly feed the score back as damage. | Compare scalar, component vector and no score; test overlap, harmless debt, reversibility and sensitivity. Retain/change/remove in AE-014/015. |
| MA-11 | Informal functions explain surprising replacement effects — domain hypothesis | Role assignment, function coverage, trust/channel links and knowledge holdings are distinct. No magical transfer on replacement. Functions are discoverable via observed work and interactions. | Noncritical replacement, redundant bridge, complete transfer, interrupted work and all-agent continuity. AE-016/017/019. |
| MA-12 | Topology trade-offs can be meaningful — gameplay hypothesis | Channels have opportunity/resource costs and capacity; trust and reachability affect useful transfer. Do not encode cross-functional or hierarchical structures as always superior. | Multiple conditions with different Pareto-efficient configurations; player temptation to connect everything. AE-018/019. |
| MA-13 | Incentives can explain diverse reactions to automation — deferred hypothesis | Represent incentives and availability but do not invent broad morale/hoarding/resignation behavior for MVP. Knowledge transfer initially follows chosen actions and current capacity. Later announcement-policy experiment should compare explicit utility rules before/after replacement and allow cooperation, resistance and supervision under either actor strategy. | Revisit only if absent responses invalidate MVP choices; otherwise separate post-MVP campaign. AE-018/035. |
| MA-14 | Determinism within pinned versions is sufficient — engineering hypothesis | Integer ticks, canonical ordering, named RNG streams, versioned scenario/model/runtime, ordered command IDs. Alternative strategies can change endogenous events while sharing fixed exogenous workloads. | Canonical-history repeats, ordering boundaries, render-FPS variation and save/resume. AE-003/007/022/031. |
| MA-15 | Compressed time supports a 15–20-minute session — gameplay assumption | Player wall time and simulation ticks are distinct; observation and delivery delays use scenario units; playback rate only changes presentation/scheduling requests. | Actual participant pacing, no forced incidents, enough opportunity to respond. AE-027/029. |
| MA-16 | Small formative studies can guide design — evaluation assumption | Early cohorts of three and later five unfamiliar participants; invented thresholds predeclared in protocols. Record responses, prior familiarity, intervention and negative evidence. These samples cannot estimate population engagement or validate organizational science. | Independent readbacks, voluntary strategy retry, neutral prompts and later replication. AE-011/019/029/030. |

For every numeric parameter introduced later, record the following beside the
scenario or experiment configuration. Missing provenance means **toy**, never
silently “empirical.”

| Field | Required content |
| --- | --- |
| `parameter_id`, `assumption_id` | Stable name and register entry |
| `value`, `unit`, `range` | Value, meaningful units, admissible bounds and sensitivity range |
| `classification` | `product_constraint`, `toy_gameplay`, `structural_hypothesis`, `engineering_budget`, or `empirically_calibrated` |
| `rationale`, `source` | Why this value exists; source is explicitly “invented for experiment” until evidence exists |
| `calibration_version` | Null for toy values; source dataset/version and method if calibrated later |
| `uncertainty`, `alternatives` | What is unknown; plausible alternative mechanism or parameterization |
| `review_activity` | Next activity responsible for testing the assumption |

An experiment protocol records its question, hypotheses and falsifiers, controls,
seed set, workload-sharing scheme, command strategies, metrics, parameter changes,
raw artifact names and interpretation limits before results are analyzed. Reports
include all tested seeds, variability and counterexamples. Do not discard a run
because it fails to tell the expected Sarah story.

Independent evidence means independence of relevant sources/methods, not merely a
second actor or second test file. A simulation reviewer checks model consistency;
a participant provides usability evidence; neither role establishes empirical
organizational truth. Update this register when a mechanism is removed as well as
when one is added.
