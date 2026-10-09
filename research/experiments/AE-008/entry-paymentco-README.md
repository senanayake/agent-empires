# PaymentCo scenario design brief

This is an authored planning fixture, not an implemented or calibrated scenario.
AE-008 creates `scenario.yaml` and its schema after the headless mechanism passes.
The [campaign](../../docs/mvp-campaign.md) is the authority for sequencing.

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

AE-008 records numeric units, source classification, schema version, seed support,
holding accessibility and initial graph. Do not create an executable YAML file
before deciding how those concepts are validated.
