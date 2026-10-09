# PaymentCo scenario design brief

AE-008 supplies authored inputs in [scenario.json](scenario.json), validated by
[schema.json](schema.json) and the application loader. JSON replaces the planned
YAML filename under the packet's explicit format alternative; see
[ADR-010](../../docs/adr/0010-scenario-format.md). These are fictional inputs, with
no empirical calibration or implemented payment outcome rules. The
[campaign](../../docs/mvp-campaign.md) remains the authority for sequencing.

**Intent:** Improve customers' ability to finish payment.
**Goal:** Reduce failed-payment abandonment, measured per eligible payment attempt
over an explicit observation window. Track duplicate charges, retry cost, audit
coverage and latency separately; do not collapse them into a moral score.
**Work Item:** “Retry failed payments.”

### Initial organizational distribution

These ten fictional humans and assignments are proposed starting data. The
functions are simulation inputs; players discover them through observable work
and conversations, not an omniscient inventory of every hidden fact.

| ID / actor | Department / formal role | Initially held information or informal function |
| --- | --- | --- |
| `maya` / Maya | Product / product lead | Abandonment goal and authority over success measures; customer-priority trade-offs |
| `leo` / Leo | Product / analyst | Incomplete customer/workload observations; access to validation feedback |
| `ada` / Ada | Architecture / architect | Idempotency/interface rationale and architecture decision authority |
| `omar` / Omar | Architecture / systems engineer | Backoff/load interactions; bridge to Operations |
| `priya` / Priya | Security / risk lead | Audit policy and scoped risk authority |
| `noah` / Noah | Security / assurance analyst | Verification limitations, audit observations and evidence lineage |
| `sarah` / Sarah | Engineering / senior engineer | Sole tacit historical rationale behind decline handling; Product/Engineering translator and incident historian |
| `jin` / Jin | Engineering / developer | Repository/implementation knowledge; less historical domain context |
| `elena` / Elena | Operations / reliability lead | Production feedback channel, incident observations and operational authority |
| `ben` / Ben | Operations / support analyst | Failure categories, support observations and contact with affected users |

Sarah is an example carrier of state, never an event-rule condition. Moving those
holdings/functions to a different actor must move the causal vulnerability too.
Some knowledge has redundant holders; some exists only as tacit information. An
initial decline policy may be explicit while its crucial scope/rationale is tacit.
The thin Work Item does not automatically copy either into Engineering.

At most three agent profiles: implementer, investigator, and assurance/operations
assistant. These are capability bundles within Actor, not distinct rule engines.
Start with one implementer profile in C2. An agent has no **inherent** authority
but can receive recognized delegated authority, acquire holdings, own functions,
and maintain operational feedback. Humans and agents can both make mistakes.

### Six distributed decisions

| Decision ID | Question / illustrative alternatives | Initial source and authority / uncertainty |
| --- | --- | --- |
| `retryable_types` | Transient only; all failures; selected categories | Ben knows failure observations; Product/Engineering must agree scope. Categories do not automatically reveal recovery probabilities. |
| `retry_count` | None; one; three; bounded adaptive count | Maya owns customer trade-offs; Leo has partial evidence. No count is universally correct. |
| `backoff` | Immediate; fixed; exponential/capped | Omar has load knowledge, Ada architecture context, Operations runtime evidence. |
| `idempotency` | Reuse a stable operation key; new key on each attempt; unspecified | Ada knows the interface contract and rationale; implementation may omit it when context is absent. |
| `declined_handling` | Do not retry; retry selected soft declines; retry all | Initial fictional policy says not to retry declines; Sarah knows historical scope/rationale. Policy authority and world truth are separate. |
| `audit_requirement` | Record attempt lineage; summary only; none | Priya owns the policy; Noah can assess conformance. Green unit tests do not establish audit compliance. |

Keep decision alternatives, source holdings and authority references explicit.
Content lost from the organization stays in the private scenario/audit for replay,
but is unavailable to actor policies and player snapshots until re-learned.

### World and belief variants

**World A:** Enough transient failures recover after a delay to make retries
valuable; hard declines remain unhelpful to retry; duplicate execution is possible
when the deployed behavior lacks idempotency. Observation latency can conceal
harm while throughput appears good. All rates and costs are invented parameters.

**World B:** Failure mix or customer response differs. Evidence may justify a
narrow class of retried soft declines or a different retry/backoff policy. The
initial blanket rule can be wrong for the goal. This is another toy environment,
not a claim about real payment practice. Hold world samples fixed when comparing
strategies within a variant, and record environmental changes separately.

Outcome code sees deployed behavior and exogenous workload. It must not branch on
Sarah's name, an automation percentage, or a “player chose wrong” flag. An incident
requires modeled exposure; no traffic means no transaction incident.

### Required scenario contrasts

1. Fast inference produces green verification while interpretation stays unknown.
2. Unprepared replacement loses a holding or bridge; consequences occur only if
   subsequent work/world events expose the resulting unsupported decision.
3. Clarification or documentation prevents that gap, at a visible time/resource cost.
4. An unsupported low-impact choice is harmless; additional ceremony can cost more.
5. Human-only, hybrid, and fully agent-operated organizations each produce plausible
   runs; full automation can succeed with preserved authority and feedback.
6. Production evidence challenges an authorized policy and triggers genuine learning.

### Authored input contract (AE-008)

Load from the repository root using `load_scenario` in
`agent_empires.application.scenarios`. It checks strict UTF-8 JSON, schema version
1, scenario version major 1, model version `paymentco-inputs-v1`, typed IDs and
references, numeric bounds/units, provenance and scoped policy authority. Its
`sha256` is the exact file-byte hash; pass `expected_hash` from a trusted run
manifest to reject changed inputs. Formatting changes also change this hash.
There is no executable code, YAML tag, alias, implicit timestamp or live API.

The ten actors above initially use the `human` capability profile. `implementer`,
`investigator` and `assurance_ops` are the three optional agent profiles. All four
use the same preference/capability schema and AE-006 `CapabilityProfile` API.
Profile speed, cost and availability are authored parameters for later work rules;
loading does not execute work or select a decision. Actor kind grants nothing.
Roles, discoverable functions, explicit grants and holdings remain separate.

The initial directed graph is Maya→Sarah→Jin, Ben→Sarah, Ada→Jin,
Omar→Elena→Leo→Maya, and Priya→Noah→Jin. Every edge refers to explicit
latency, capacity, cost, trust, loss and distortion parameters. Loading does not
send a message. Distortion is zero in this v1 input because no syntactic
replacement rule has been authored. Connectivity itself supplies no knowledge.

Goal target is 0.1 abandoned attempts per eligible attempt over 100 ticks, an
invented target, with no assertion that it is achievable. The work item remains
thin. Initial policies select `do_not_retry` declines and `attempt_lineage` audit,
with Priya's matching grants and separately held policy claims. Policy data does
not resolve the other decisions or provide world evidence.

World A's conditional failure mix (transient / soft decline / hard decline /
ambiguous) is 0.40 / 0.20 / 0.15 / 0.25; World B's is 0.25 / 0.30 / 0.20 /
0.25. Their illustrative per-category recovery parameters are 0.65 / 0.02 / 0 /
0.40 and 0.30 / 0.60 / 0 / 0.20. These inputs alone do not define arrival,
retry, backoff or customer response rules; AE-010 must decide and test those
rules. Neither world is selected implicitly by the loader. A run must explicitly
pin the variant, file hash, engine/runtime versions, root seed and ordered commands.

`audit_data()` is private trusted setup data. `snapshot_for(actor_id)` exposes
public goal values, the thin work item, formal roster and decision alternatives,
plus only that actor's accessible personal or readable artifact holdings.
It excludes world parameters, policy catalog, source registry, decision source
references, informal functions and other actors' claims. The artifact
`incident_archive` initially has no readers. Sarah alone holds `historical_scope`;
Jin does not receive it merely because it is stored in the input. The independent
[Jin snapshot fixture](jin-snapshot.json) records the expected initial projection.
Snapshots describe initial access; runtime services must use fresh live store
views after transfer, revocation or departure.

All operational numbers carry the assumption ID, unit, range, sensitivity range,
classification, rationale, invented source, null calibration version, uncertainty,
alternative and review activity. Versions and other structural metadata are not
operational parameters. No input is marked empirically calibrated. See the
[model contract](../../docs/simulation-model.md) and
[AE-008 review](../../research/experiments/AE-008/review.md) for limits and ledger.
