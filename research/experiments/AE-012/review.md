# AE-012 self-review and scoped ledger

Reviewer: assigned Codex worker, self-review. Disposition: pass for the bounded
clarification operation and toy comparison; no architecture or human acceptance.
No mechanism removed. No ADR change: this operation follows the existing integer
clock, provenance and simulation import constraints.

At entry the tree was clean and the locked checkout used CPython 3.12.13. AE-011's
receipt checker passed. Review covered its renderer/reader artifacts, original
study protocol, missing participant finding, engineering/operator review and the
owner-approved scope revision. Original defer/delivery records are historical;
the current receipt accepts engineering under owner direction and permits AE-012,
with comprehension/enjoyment deferred to AE-029. The present operation depends on
that tested rendering boundary, not a claimed reader success. Updating MA-09 makes
older assumptions-file hash bindings historical; exact entry assumptions and the
predecessor receipt are preserved here. No predecessor receipt was rewritten.

The holder answers from a fresh accessible view at response time, never from the
private catalog/world. Round-trip latency, earliest availability, service time,
request congestion and answer capacity all affect delivery. Accepted answer
batches snapshot access at response time; later sender revocation/departure does
not recall that batch, matching AE-005 admission semantics. Recipient departure
prevents acquisition. Exact-deadline arrivals precede timeout; partial holdings
and negative results survive. Request loss waits to timeout; answer loss produces
a no-answer completion. Freshness is explicit authored metadata, not age decay.
Question references are typed; syntactic distortion applies only to answer claims.

Answer provenance includes acquisition/access lineage and ultimate source roots.
Rejected authority IDs survive in the audit. A valid answer authority field means
that the holder's grant covers actor, scope, option and current receipt tick;
it does not prove truth, a separately issued authorization, or requester delegation.
Choices cite the answer and preserve prior sources. Reports used as rationale
are not recast as independent validation. Conflicts remain explicit and do not
become majority votes; stale claims remain visible but this policy ignores them.

The predeclared protocol yielded 512 pairs / 1,024 trajectories over 16 seeds,
two worlds, eight conditions and two timing profiles. All workload/world/state,
kind, stale, no-exposure, authority and independence controls passed. Seed-zero
histories and every pair/history/workload hash are retained. Fresh replay compares
canonical results in temporary storage and checks the 120-second local budget.

Concrete findings (cost changes are clarification minus inference):

- World A helpful fast answers reduce mean duplicates by 0.875 and retry resources
  by 1.875, with three ticks and two channel units added. At duplicate penalty 20
  and delay weight 1, mean cost changes by −14.375; asking wins on nine seeds and
  loses on seven. With penalty 5/delay 4 it loses on fourteen seeds (mean +7.75).
- Slow helpful answers add eight ticks. Under penalty 5/delay 4 every World A seed
  loses (mean +27.75). World B helpful fast mean duplicate reduction is only 0.1875;
  penalty 20/delay 1 gives mean −0.0625, with thirteen losing seeds. A favorable
  mean therefore does not imply reliable benefit.
- Wrong answers reverse safe inference into new keys: World A fast adds mean
  0.875 duplicates; penalty 20/delay 1 costs +24.375. Valid holder rights do not
  protect against wrong information. Conflicting answers leave preference unchanged,
  cost three channel units/four fast ticks, and retain both same-root alternatives.
- Unavailable holders time out after twelve ticks. Stale answers arrive but do not
  change the option. Out-of-scope answers can improve behavior with invalid authority;
  usefulness and legitimacy stay separate. Lossy fast World A answers give mean
  +0.8125 cost at penalty 20/delay 1 and only two winning seeds.
- Harmless inference has zero duplicate exposure. Asking gains no physical outcome
  or retry-resource benefit in any seed, and always costs more with positive delay
  weights (fast +5, slow +10 at delay weight 1). Incident-free unsupported seeds,
  ties, reversals and all failed utility comparisons remain in `results.json`.

These findings support a conditional trade-off in this model. Asking is worthwhile
only when the modeled avoided consequence/resource cost exceeds channel and waiting
cost. It cannot be asserted as a generally optimal strategy, and answer correctness
is never supplied to the actor by the experiment's world owner. Goal abandonment
and completion are unchanged here; no claim of general goal improvement follows.

Actual TDD negatives are retained: missing learning module; colliding answer-task
IDs in a three-answer batch; lost acquisition lineage after access restoration;
missing experiment module; and omitted rejected-grant IDs. Each was fixed and the
focused suite is green. The initial numerical run is compressed under `initial-run/`
for history; final current source/hash evidence is the top-level results/traces.
CLI tests also preserve overwrite refusal, tamper rejection and a deliberately
zero-budget failure in temporary test storage. No reviewed evidence is overwritten.

Limits: invented parameters; finite exact claims; no dialogue/LLM; no shared actor
availability queue; no empirical source authentication; no universal performance
claim. Workload arrivals remain relative to deployment. Delay cost is an explicitly
invented opportunity-cost proxy, not observed predeployment customer loss or a
physical penalty added to the payment engine. General belief/policy/goal learning
remains AE-013. No human sessions, integration or publication are claimed.

| Activity | Repository disposition | Controller disposition |
| --- | --- | --- |
| AE-012 | Clarification, focused tests, predeclared comparison and current evidence delivered; local Git outcome recorded separately. | Independent validation and local promotion remain controller-owned; no push. |

The shared ledger is outside this launch's exact allowed paths; this is the scoped
handoff ledger. Recommend AE-013 only after AE-012 delivery/validation. No successor
was executed, and no campaign completion is declared.

Local delivery failed on the single staging attempt: Git could not create
`/home/senanayake/Dev/agent-empires/.git/worktrees/AE-012-20261009T034201Z/index.lock`
because the shared metadata filesystem is read-only. `delivery.json` preserves
exit 128 and the exact error. Commit was not attempted after staging failed;
no retry, push, remote/hook change or integration occurred. The final worker
status is failed for the required local delivery, while the reviewed source and
research disposition remains pass. Operator hash-reviewed delivery recovery is
required before recommending/executing a successor.
