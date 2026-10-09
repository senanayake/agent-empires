# AE-013 review and scoped handoff ledger

Reviewer: assigned Codex worker, self-review. Disposition: pass for the bounded
finite loops and engineering evidence; no architecture, domain or human acceptance.
No mechanism removed. ADR-006/008 remain proposed, with implementation evidence
added. The shared build/handoff ledger is outside the exact allowed paths, so this
document supplies the scoped ledger.

Entry tree was clean on the assigned campaign branch. Locked offline setup used
the pre-cached dependencies and checkout-local CPython 3.12.13. AE-012's current
receipt check passed. Substantive review covered its clarification implementation,
focused tests, raw 512-pair result structure (zero failed controls), traces,
protocol, worker limitations and independent operator review. Holder claims can
be wrong, shared or unavailable; receipt does not authorize the requester or
validate interpretation fitness. Its former worker delivery failure is historical;
the artifacts and reviewed receipt are present in this checkout. Entry receipt
and assumptions copies preserve bindings before legitimate successor edits.

The authored loops change separate objects:

- Implementation: `proposal.broken@1` becomes `proposal.fixed@1`, with every
  decision version and the work item unchanged. Missing retries fail the chosen
  specification; the fix passes. Old failing proposal and checks survive.
- Requirement: `idempotency@1` (`new_key`) becomes `idempotency@2` (`stable_key`)
  after an accessible current report from an independent declared interface root.
  Support changes while authority remains inferred. Both deployed artifacts pin
  their original choices. An authored ambiguous exposure produces one duplicate
  for the old artifact and zero for the corrected future artifact. The report is
  trusted authored evidence, not an authenticated real-world source.
- Policy: authorized `declined_handling@1` (`do_not_retry`) misses the unchanged
  goal in four observed soft-decline operations. After delayed observations,
  Priya's current scoped grant permits `declined_handling@2` (`soft_only`). This
  interpretation starts with no independent support and an explicit fitness gap.
  Future deployment with the same workload recovers all four operations and
  passes its own observation assessment. Old deployment/goal/choice versions and
  the complete prefix history remain unchanged.

The finite rule is deliberately conservative: all admitted operations must have
observations inside the physical goal window; fewer than four samples stays
pending; rate at/below target passes; a miss of at least 0.2 fails; a smaller miss
is unknown. Copies of an observed operation never increase sample count. This
is a toy policy-review threshold, not a posterior, confidence interval or causal
diagnosis. Threshold comparisons use decimal rational arithmetic to preserve
the exact boundary. Window outcomes arriving late still describe the old version.

Negative controls cover insufficient/noisy/confirming evidence, verification used
as validation, shared-source reports, contradictions, access/freshness, forged
assessments, invalid parameters, cherry-picked incomplete cohorts, revoked or
wrong scoped authority, policy-path bypass and delayed version mismatch. Report
repetition produces the same single backed root and status, not a majority vote.
The minimum/margin provenance is in `parameters.json`; sensitivity remains AE-015.

Sixteen paired seeded World B controls retain the same workload across old/future
deployments. Fourteen old deployments fail the review rule and justify a revision;
two remain unknown and are not revised. Eight revised deployments still fail,
six remain unknown, and zero pass the original goal target. These results prevent
a generally effective-remedy claim despite the authored positive example. They
are generated toy outcomes, not independent empirical samples or real payment
recommendations. Raw observations, assessment versions and workload/history hashes
remain in `loop-traces.json`; replay verifies exact canonical bytes without
overwriting evidence. No failed seeds are removed.

Actual red results are preserved: missing APIs; a fixture that selected no retries
(so the omitted-retry defect was harmless); a float boundary exclusion; and a
requirement-path policy bypass. Fixing the fixture was an explicit correction,
not threshold tuning. A trace-author schema-key typo and its traceback also remain.
Focused tests and broader regression results are recorded separately. All three
histories explicitly assert unchanged prefix events.

Limits: trusted finite semantic report labels/source roots; no empirical source
authentication; complete-cohort assessment without a streaming estimator;
four-sample/margin rules have no statistical calibration; physical samples can
be correlated; a goal miss does not establish which choice caused it. Arbitrary
goals, automated alternative discovery, retrospective rewriting and real human
evidence remain outside this activity. No integration/publication is asserted.

| Activity | Repository disposition | Controller disposition |
| --- | --- | --- |
| AE-013 | Finite loops, tests, raw/reproducible traces, assumption/ADR updates and reviewed receipt delivered; local Git outcome is reported separately. | Independent execution validation and local integration remain controller-owned; push is disabled. |

Recommend AE-014 only after successful local delivery and controller validation.
No successor was executed, and no campaign completion is declared.

Local delivery failed on the single permitted staging attempt: Git returned 128
because it could not create
`/home/senanayake/Dev/agent-empires/.git/worktrees/AE-013-20261009T040058Z/index.lock`
on the read-only shared filesystem. `delivery.json` retains the actual command
and error. Commit was not attempted after staging failed; no retry/push occurred.
The engineering receipt remains pass, but final worker status is failed for the
required local commit. Operator hash-reviewed delivery recovery is needed before
advancing; the worker's next recommendation is null.
